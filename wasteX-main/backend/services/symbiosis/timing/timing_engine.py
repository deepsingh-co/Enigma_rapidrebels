from typing import Dict, Any, Optional, Tuple
from datetime import datetime, date


class TimingAvailabilityEngine:
    """
    Evaluates temporal compatibility and supply-demand scheduling overlap
    between waste producers and receiving industrial partners.
    """

    @classmethod
    def evaluate_timing(
        cls,
        producer_qty: float,
        producer_frequency: str = "monthly",
        producer_start_day: int = 1,
        producer_end_day: int = 10,
        receiver_demand_qty: float = 5000.0,
        receiver_frequency: str = "monthly",
        receiver_start_day: int = 1,
        receiver_end_day: int = 15,
        producer_available_from: Optional[str] = None,
        producer_available_until: Optional[str] = None,
        receiver_required_from: Optional[str] = None,
        receiver_required_until: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes timing compatibility status, scheduling overlap, and numerical score.
        """
        # 1. Frequency Alignment
        freq_weights = {
            "daily": 30,
            "weekly": 4,
            "monthly": 1,
            "one-time": 0
        }

        p_freq_norm = (producer_frequency or "monthly").lower()
        r_freq_norm = (receiver_frequency or "monthly").lower()

        frequency_matched = (p_freq_norm == r_freq_norm)
        frequency_note = "Exact matching recurring cycle" if frequency_matched else f"Producer dispatch ({p_freq_norm}) vs Receiver intake ({r_freq_norm})"

        # 2. Window Day Overlap (e.g. 1st-5th vs 1st-10th)
        p_start = max(1, min(31, int(producer_start_day)))
        p_end = max(p_start, min(31, int(producer_end_day)))
        r_start = max(1, min(31, int(receiver_start_day)))
        r_end = max(r_start, min(31, int(receiver_end_day)))

        # Overlap interval [max(start), min(end)]
        overlap_start = max(p_start, r_start)
        overlap_end = min(p_end, r_end)

        has_day_overlap = overlap_start <= overlap_end
        overlap_days = max(0, overlap_end - overlap_start + 1) if has_day_overlap else 0

        # 3. Calendar Date Overlap if explicit dates are given
        date_conflict = False
        if producer_available_from and receiver_required_until:
            try:
                p_from = datetime.fromisoformat(producer_available_from).date()
                r_until = datetime.fromisoformat(receiver_required_until).date()
                if p_from > r_until:
                    date_conflict = True
            except Exception:
                pass

        if producer_available_until and receiver_required_from:
            try:
                p_until = datetime.fromisoformat(producer_available_until).date()
                r_from = datetime.fromisoformat(receiver_required_from).date()
                if p_until < r_from:
                    date_conflict = True
            except Exception:
                pass

        # 4. Quantity Overlap
        qty_overlap = min(producer_qty, receiver_demand_qty)
        pct_demand_covered = (qty_overlap / max(1.0, receiver_demand_qty)) * 100.0

        # 5. Timing Compatibility Classification & Score
        if date_conflict:
            timing_compatible = False
            status = "Timing Conflict"
            score = 25.0
            explanation = "Date window mismatch between producer availability and receiver demand deadline."
        elif overlap_days == 0:
            timing_compatible = False
            status = "Timing Conflict"
            score = 20.0
            explanation = f"Zero scheduling overlap: Producer dispatch cycle (Days {p_start}–{p_end}) does not overlap with receiver intake window (Days {r_start}–{r_end}). Scheduling conflict prevents direct batch coordination."
        elif has_day_overlap and frequency_matched:
            timing_compatible = True
            status = "Timing Compatible"
            score = 95.0
            explanation = f"Fully compatible schedule: Producer available days {p_start}–{p_end} overlaps with receiver intake window days {r_start}–{r_end} ({overlap_days} days buffer)."
        elif has_day_overlap:
            timing_compatible = True
            status = "Partially Compatible"
            score = 80.0
            explanation = f"Partially compatible: {frequency_note} with {overlap_days} days schedule overlap. Buffer staging enables continuous fulfillment."
        else:
            timing_compatible = False
            status = "Timing Conflict"
            score = 20.0
            explanation = f"Producer cycle ({p_start}–{p_end}) does not overlap receiver window ({r_start}–{r_end}); timing conflict requires schedule realignment."

        return {
            "timing_compatible": timing_compatible,
            "status": status,
            "timing_score": round(score, 1),
            "frequency_alignment": frequency_note,
            "producer_schedule": f"{p_freq_norm.capitalize()} (Days {p_start}–{p_end})",
            "receiver_schedule": f"{r_freq_norm.capitalize()} (Days {r_start}–{r_end})",
            "scheduling_overlap_days": overlap_days,
            "quantity_overlap_kg": round(qty_overlap, 1),
            "demand_coverage_percent": round(pct_demand_covered, 1),
            "explanation": explanation
        }
