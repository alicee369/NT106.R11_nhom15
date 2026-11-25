import math
from typing import List, Optional, Tuple


def estimate_required_score(
    current_scores: List[dict],
    remaining_weight_percent: float,
    target_gpa: float,
    scale: float,
) -> Tuple[bool, Optional[float], str]:
    """
    Tính điểm cần đạt cho phần tỷ trọng còn lại để hoàn thành mục tiêu GPA.
    Trả về tuple: (is_valid_and_achievable, required_score, message)
    """
    if not all(
        math.isfinite(val)
        for val in (remaining_weight_percent, target_gpa, scale)
    ):
        return False, None, "Định dạng dữ liệu số không hợp lệ."

    if scale <= 0:
        return False, None, "Thang điểm không hợp lệ (phải lớn hơn 0)."
    if target_gpa < 0 or target_gpa > scale:
        return False, None, "Mục tiêu GPA nằm ngoài thang điểm cho phép."
    if remaining_weight_percent <= 0 or remaining_weight_percent > 100.0 + 1e-6:
        return False, None, "Tỷ trọng phần còn lại phải lớn hơn 0% và không vượt quá 100%."

    current_weight = 0.0
    weighted_sum = 0.0

    for item in current_scores:
        score = float(item["score"])
        weight = float(item["weightPercent"])
        if not (math.isfinite(score) and math.isfinite(weight)):
            return False, None, "Điểm số hoặc tỷ trọng chứa giá trị không hợp lệ."
        if score < 0 or score > scale or weight < 0:
            return False, None, "Điểm số hoặc tỷ trọng hiện tại không hợp lệ."
        current_weight += weight
        weighted_sum += score * weight

    total_weight = current_weight + remaining_weight_percent
    if total_weight > 100.0 + 1e-6:
        return False, None, "Tổng tỷ trọng phần trăm không được vượt quá 100%."

    required = (target_gpa * total_weight - weighted_sum) / remaining_weight_percent

    if required > scale + 1e-9:
        return False, None, "Mục tiêu không khả thi với số điểm hiện tại."

    clamped = max(0.0, round(required, 2))
    return True, clamped, "Thành công."