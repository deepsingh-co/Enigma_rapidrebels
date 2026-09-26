from typing import Dict, Any, List, Optional, Tuple


class ProcessingRequirementEngine:
    """
    Evaluates preprocessing feasibility, complexity, and technical compatibility
    for converting industrial waste streams into target secondary resources.
    """

    # Comprehensive matrix of industrial conversion processes & preprocessing steps
    PROCESSING_PROFILES = {
        "fly ash": {
            "processes": [
                {
                    "target_use": "Cement & Concrete Clinker Replacement",
                    "requires_preprocessing": True,
                    "steps": ["Dry screening (<45 µm) for fineness control", "Moisture verification (<1%)", "Carbon loss-on-ignition check"],
                    "complexity": "Low",
                    "receiver_direct_accept": True,
                    "score_penalty": 0.0,
                    "explanation": "Receiving cement mills possess integrated pneumatic blending silos and can accept dry fly ash directly without third-party treatment."
                },
                {
                    "target_use": "Autoclaved Aerated Concrete (AAC) & Bricks",
                    "requires_preprocessing": True,
                    "steps": ["Wet slurry ball-milling", "Lime/gypsum proportioning", "Aluminum powder foaming agent addition"],
                    "complexity": "Medium",
                    "receiver_direct_accept": True,
                    "score_penalty": 5.0,
                    "explanation": "Brick plants require slurry mixing and high-pressure autoclaving on-site."
                },
                {
                    "target_use": "Geopolymer & Ceramic Synthesis",
                    "requires_preprocessing": True,
                    "steps": ["Alkaline activator preparation (NaOH/Na₂SiO₃)", "High shear thermal blending", "Curing at 60-80°C"],
                    "complexity": "High",
                    "receiver_direct_accept": False,
                    "score_penalty": 15.0,
                    "explanation": "Requires specialized chemical activation equipment and thermal curing ovens."
                }
            ]
        },
        "slag": {
            "processes": [
                {
                    "target_use": "GGBFS Ground Granulated Blast Furnace Slag",
                    "requires_preprocessing": True,
                    "steps": ["Magnetic iron extraction", "Rotary dryer dewatering", "Vertical roller mill grinding"],
                    "complexity": "Medium",
                    "receiver_direct_accept": True,
                    "score_penalty": 5.0,
                    "explanation": "Slag grinding units have dedicated roller mills for fine pulverization."
                },
                {
                    "target_use": "Road Base & Highway Aggregate",
                    "requires_preprocessing": True,
                    "steps": ["Jaw crushing & screening", "Weathering stabilization for free-lime hydration"],
                    "complexity": "Low",
                    "receiver_direct_accept": True,
                    "score_penalty": 2.0,
                    "explanation": "Standard mobile aggregate crushers can process slag at the job site."
                }
            ]
        },
        "cotton": {
            "processes": [
                {
                    "target_use": "Acoustic & Thermal Insulation Pads",
                    "requires_preprocessing": True,
                    "steps": ["Mechanical garnetting/shredding", "Bicomponent polymer fiber blending", "Oven thermal bonding"],
                    "complexity": "Medium",
                    "receiver_direct_accept": True,
                    "score_penalty": 5.0,
                    "explanation": "Insulation manufacturers have specialized fiber opening and needle-punching lines."
                },
                {
                    "target_use": "Regenerated Yarn Spinning",
                    "requires_preprocessing": True,
                    "steps": ["Color manual sorting", "Rotary blade cutting", "Carding and drawing"],
                    "complexity": "Low",
                    "receiver_direct_accept": True,
                    "score_penalty": 2.0,
                    "explanation": "Recycled open-end spinning mills directly take sorted cotton cuttings."
                }
            ]
        },
        "biomass": {
            "processes": [
                {
                    "target_use": "Drop-in Biofuels & Pyrolysis Bio-Oil",
                    "requires_preprocessing": True,
                    "steps": ["Drying to <10% moisture", "Hammer-mill pulverization to <2mm", "Fast pyrolysis reactor feeding"],
                    "complexity": "High",
                    "receiver_direct_accept": False,
                    "score_penalty": 12.0,
                    "explanation": "Biorefineries require strict moisture (<10%) and fine particle size for reactor fluidization."
                },
                {
                    "target_use": "Boiler Fuel / Bio-Pellets",
                    "requires_preprocessing": True,
                    "steps": ["Solar/rotary drying", "Ring-die pelletizing"],
                    "complexity": "Medium",
                    "receiver_direct_accept": True,
                    "score_penalty": 5.0,
                    "explanation": "Biomass power stations accept both raw and pelletized agro residues."
                }
            ]
        },
        "plastic": {
            "processes": [
                {
                    "target_use": "Compounded Engineering Thermoplastics",
                    "requires_preprocessing": True,
                    "steps": ["Optical NIR flake sorting", "Hot caustic wash to remove adhesives", "Twin-screw extrusion compounding"],
                    "complexity": "Medium",
                    "receiver_direct_accept": True,
                    "score_penalty": 6.0,
                    "explanation": "Plastic recyclers have integrated washing and regranulation plants."
                }
            ]
        },
        "concrete": {
            "processes": [
                {
                    "target_use": "Recycled Concrete Aggregate (RCA)",
                    "requires_preprocessing": True,
                    "steps": ["Hydraulic breaker reduction", "Cross-belt magnetic iron separator", "Multi-deck screen sizing"],
                    "complexity": "Low",
                    "receiver_direct_accept": True,
                    "score_penalty": 2.0,
                    "explanation": "Civil infrastructure contractors deploy mobile on-site crushers."
                }
            ]
        }
    }

    @classmethod
    def evaluate_processing(
        cls,
        material: str,
        target_resource: str,
        condition: str = "dry",
        form: str = "solid",
        transforming_process: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluates processing feasibility, complexity score, and receiving facility direct-intake capability.
        """
        mat_lower = (material or "").lower()
        res_lower = (target_resource or "").lower()
        cond_lower = (condition or "").lower()
        proc_lower = (transforming_process or "").lower()

        # Find matching material profile
        matched_profile = None
        for key, p_dict in cls.PROCESSING_PROFILES.items():
            if key in mat_lower:
                matched_profile = p_dict
                break

        if matched_profile and matched_profile.get("processes"):
            # Find best matching process
            best_proc = matched_profile["processes"][0]
            for p in matched_profile["processes"]:
                if any(w in res_lower for w in p["target_use"].lower().split()):
                    best_proc = p
                    break

            req_preproc = best_proc["requires_preprocessing"]
            steps = list(best_proc["steps"])
            complexity = best_proc["complexity"]
            direct_accept = best_proc["receiver_direct_accept"]
            explanation = best_proc["explanation"]
            score_penalty = best_proc["score_penalty"]
        else:
            # Domain heuristic fallback
            req_preproc = True
            steps = ["Quality assay and contaminant screening", "Uniform sizing / conditioning"]
            complexity = "Low" if "pure" in cond_lower or "dry" in cond_lower else "Medium"
            direct_accept = True
            explanation = f"Standard industrial intake processing for {material} into {target_resource}."
            score_penalty = 5.0

        # Adjust for poor initial condition
        if "mixed" in cond_lower or "contaminated" in cond_lower:
            steps.insert(0, "Pre-sorting to remove extraneous contaminants")
            complexity = "High" if complexity == "Medium" else "Medium"
            score_penalty += 8.0
            direct_accept = False
        elif "wet" in cond_lower or "slurry" in cond_lower:
            if "thermal" in proc_lower or "cement" in res_lower:
                steps.insert(0, "Thermal drying / mechanical dewatering stage")
                score_penalty += 6.0

        # Numerical Processing Score (0-100)
        base_score = 95.0 - score_penalty
        processing_score = min(100.0, max(45.0, base_score))

        return {
            "requires_preprocessing": req_preproc,
            "preprocessing_steps": steps,
            "processing_complexity": complexity,
            "receiver_can_accept_directly": direct_accept,
            "processing_score": round(processing_score, 1),
            "technical_explanation": explanation
        }
