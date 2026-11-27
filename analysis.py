"""Recalculate the manuscript's principal point estimates using Python 3.9+."""
import argparse
import csv
from fractions import Fraction
import json
from math import fsum, log2
from pathlib import Path
from statistics import mean

INPUT = Path(__file__).with_name("analysis-input.csv")
DOMAINS = "ABCDEFGH"
SHARED = "ACDEFGH"
TAGS = ("strict", "expanded")
SOURCES = {"CHIMA": ("SRE", "EPSP", "HPD", "SLPA"), "DMHC": ("EPSP", "HPD", "SLPA")}
PERIODS = ("2021–2022", "2023–2024", "2024–2025")
FIELDS = "block frame period observation scheme group category numerator denominator".split()

def read_input(path):
    groups = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDS:
            raise ValueError("Unexpected input columns")
        for line, r in enumerate(reader, 2):
            key = tuple(r[name] for name in FIELDS[:6])
            group = groups.setdefault(key, {})
            num, den = Fraction(r["numerator"]), Fraction(r["denominator"])
            count_only = r["block"] in {"matching_flow", "lot_overlap"}
            invalid = den <= 0 or num < 0 or (count_only and den != 1) or (not count_only and num > den)
            if r["category"] in group or invalid:
                raise ValueError(f"Invalid or duplicate input at line {line}")
            group[r["category"]] = (num, den)
    return groups

def integer(value):
    if value.denominator != 1:
        raise ValueError("Expected an integer count")
    return int(value)

def ratio_cell(cell):
    n, d = cell
    return {"numerator": integer(n), "denominator": integer(d), "pct": float(100*n/d)}

def profile(group):
    denominators = {d for _, d in group.values()}
    if len(denominators) != 1 or sum(n for n, _ in group.values()) != next(iter(denominators)):
        raise ValueError("Domain weights do not add to the classifiable total")
    return {k: n/d for k, (n,d) in group.items()}

def jsd(p, q, domains):
    """Jensen–Shannon divergence in bits. Normalise each profile on the selected domains."""
    x, y = [[float(v[k] / sum(v[j] for j in domains)) for k in domains] for v in (p,q)]
    m = [(a+b)/2 for a,b in zip(x,y)]
    def kl(v):
        return fsum(a*log2(a/b) for a,b in zip(v,m) if a)
    return (kl(x)+kl(y))/2

def estimate(groups):
    out = dict(cross_section={}, jsd={}, matched={}, survey={}, annual_awards={}, budget={}, overlap={})
    for frame, sources in SOURCES.items():
        profiles = {}
        by_obs = {}
        for obs in sources:
            def get(block, scheme, subgroup=""):
                return groups[block,frame,"2025",obs,scheme,subgroup]
            profiles[obs] = profile(get("profile","unit"))
            c = ratio_cell(get("coverage","unit")["classifiable"])
            item = dict(coverage=c, domain_pct={k:float(100*v) for k,v in profiles[obs].items()})
            if obs != "SLPA":
                item["ai"] = {}
                for tag in TAGS:
                    g = get("ai_state",tag)
                    states = {k:integer(v[0]) for k,v in g.items()}
                    if sum(states.values()) != c["denominator"]:
                        raise ValueError("AI state counts do not match the source sample")
                    pos = states["positive"]
                    emb = get("ai_embedding",tag)
                    bins = {k:integer(v[0]) for k,v in emb.items()}
                    n = sum(bins.values())
                    if not all(integer(d)==n for _,d in emb.values()) or n>pos:
                        raise ValueError("Inconsistent functional evidence among AI positives")
                    ai = dict(positive=ratio_cell((Fraction(pos),Fraction(pos+states["not_seen"]))),
                              states=states, classifiable_positive=n, positive_without_domain=pos-n, bins=bins,
                              any_outside_E=ratio_cell((Fraction(bins["E_plus"]+bins["outside_only"]),Fraction(n))),
                              only_outside_E=ratio_cell((Fraction(bins["outside_only"]),Fraction(n))))
                    if obs=="HPD":
                        ai["outside_domain_counts"]={k:integer(v[0]) for k,v in get("outside_coverage",tag).items()}
                    item["ai"][tag]=ai
            by_obs[obs]=item
        out["cross_section"][frame]=by_obs
        pairs={"eight_domains":{a+"-"+b:jsd(profiles[a],profiles[b],DOMAINS) for a,b in
                                (("EPSP","HPD"),("EPSP","SLPA"),("HPD","SLPA"))}}
        if frame=="CHIMA":
            pairs["seven_domains"]={a+"-"+b:jsd(profiles[a],profiles[b],SHARED) for a,b in
                                    (("EPSP","HPD"),("SRE","EPSP"),("SRE","HPD"))}
        out["jsd"][frame]=pairs
        out["budget"][frame]={}
        for tag in TAGS:
            out["budget"][frame][tag]={}
            for view in ("all","drop_top_1pct"):
                n,den=groups["budget_cny",frame,"2025","HPD",tag,view]["positive"]
                units=ratio_cell(groups["budget_count",frame,"2025","HPD",tag,view]["positive"])
                out["budget"][frame][tag][view]=dict(lots=units,positive_cny=float(n),total_cny=float(den),
                                                      pct_cny=float(100*n/den),gap_pp=float(100*n/den)-units["pct"])
    for wave in PERIODS:
        out["survey"][wave]={}
        for scheme in ("all_equal","all_selection_rate","common_selection_rate"):
            v=profile(groups["survey_profile","CHIMA",wave,"SRE",scheme,""])
            out["survey"][wave][scheme]={k:float(100*n) for k,n in v.items()}
    for year in ("2023","2024","2025"):
        key=("CHIMA",year,"SLPA","three_event_rosters","")
        cov=ratio_cell(groups[("award_coverage",)+key]["classifiable"])
        v=profile(groups[("award_profile",)+key])
        out["annual_awards"][year]=dict(coverage=cov,domain_pct={k:float(100*n) for k,n in v.items()})
    for stage in ("both","distinct_projects","each_evidenced","three_each"):
        g=groups["matching_flow","CHIMA","2025","HPD+SLPA","buyer",stage]
        out["matched"].setdefault("flow",{})[stage]={k:integer(v[0]) for k,v in g.items()}
    hospital_groups={obs:{key[-1]:value for key,value in groups.items()
                          if key[:5]==("paired_profile","CHIMA","2025",obs,"unit")} for obs in ("SLPA","HPD")}
    if hospital_groups["SLPA"].keys()!=hospital_groups["HPD"].keys():
        raise ValueError("The two matched hospital samples differ")
    sample=out["matched"]["flow"]["three_each"]
    shares={}
    for obs,role in (("SLPA","awards"),("HPD","requirements")):
        all_hosp=hospital_groups[obs]
        if len(all_hosp)!=sample["hospitals"] or sum(g["A"][1] for g in all_hosp.values())!=sample[role]:
            raise ValueError("Matched hospital or unit totals differ from the sample flow")
        vectors=[profile(g) for g in all_hosp.values()]
        shares[obs]={k:mean(v[k] for v in vectors) for k in DOMAINS}
    out["matched"]["domains"]={k:{"award_pct":float(100*shares["SLPA"][k]),"demand_pct":float(100*shares["HPD"][k]),
                                 "award_minus_demand_pp":float(100*(shares["SLPA"][k]-shares["HPD"][k]))} for k in DOMAINS}
    ov=groups["lot_overlap","CHIMA+DMHC","2025","HPD","unit",""]
    out["overlap"]={k:integer(v[0]) for k,v in ov.items()}
    if out["overlap"]["CHIMA"]+out["overlap"]["DMHC"]-out["overlap"]["shared"]!=out["overlap"]["union"]:
        raise ValueError("HPD overlap does not reconcile")
    return out

def display(results):
    for frame,by_obs in results["cross_section"].items():
        print(f"\n{frame} 2025 | Table 2 and Figures 2 and 4")
        print("Source   Mapped/Total     A      B      C      D      E      F      G      H    (%)")
        for obs,item in by_obs.items():
            c=item["coverage"]; shares=item["domain_pct"]
            cells=" ".join(f"{shares[k]:6.1f}" if k in shares else "    NM" for k in DOMAINS)
            print(f"{obs:<7} {c['numerator']:>5}/{c['denominator']:<5} {cells}")
            for tag,ai in item.get("ai",{}).items():
                v=ai["positive"]; a=ai["any_outside_E"]; b=ai["only_outside_E"]
                print(f"  {tag}: {v['numerator']}/{v['denominator']} assessable positive; "
                      f"any outside E {a['numerator']}/{a['denominator']} ({a['pct']:.1f}%); "
                      f"only outside E {b['numerator']}/{b['denominator']} ({b['pct']:.1f}%)")
        for scope,pairs in results["jsd"][frame].items():
            print(scope+" (bits): "+", ".join(f"{k} {v:.4f}" for k,v in pairs.items()))
    print("\nMatched CHIMA hospitals | Figure 2c and Table S15a")
    for stage,g in results["matched"]["flow"].items():
        print(f"{stage}: {g['hospitals']} hospitals, {g['requirements']} requirements, {g['awards']} awards")
    for k,d in results["matched"]["domains"].items():
        print(f"{k}: award {d['award_pct']:.1f}%, demand {d['demand_pct']:.1f}%, difference {d['award_minus_demand_pp']:+.1f} pp")
    print("\nSurvey Data Intelligence shares | Figure 3a")
    for wave,g in results["survey"].items():
        print(wave+": "+", ".join(f"{k} {v['E']:.1f}%" for k,v in g.items()))
    print("\nAnnual clinical-care award shares | Figure 3b")
    for year,g in results["annual_awards"].items():print(f"{year}: {g['domain_pct']['A']:.1f}%")
    print("\nVerified whole-lot planned budgets | Table S20")
    for frame,labels in results["budget"].items():
        for tag,views in labels.items():
            for view,v in views.items():
                c=v["lots"]
                print(f"{frame} {tag} {view}: {c['numerator']}/{c['denominator']} lots ({c['pct']:.1f}%), {v['pct_cny']:.1f}% of budget")
    print("\nOverlap of 2025 requirement lots:",results["overlap"])

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json",action="store_true",help="write all numeric estimates as JSON to standard output")
    args=parser.parse_args()
    results=estimate(read_input(INPUT))
    if args.json: print(json.dumps(results,ensure_ascii=False,indent=2,allow_nan=False))
    else: display(results)
