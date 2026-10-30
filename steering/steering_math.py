import math

def calculate_steering_angle(hands_landmarks):
    """
    Calculates the steering angle based on the position of two hands.
    Requires exactly 2 hands to be detected for a valid steering calculation.
    """
    if len(hands_landmarks) != 2:
        return 0, None

    # Determine which hand is left and which is right based on X coordinates
    hand1_cx = hands_landmarks[0]["lmList"][9][1] # Landmark 9 is middle finger base
    hand2_cx = hands_landmarks[1]["lmList"][9][1]

    if hand1_cx < hand2_cx:
        left_hand = hands_landmarks[0]["lmList"][9]
        right_hand = hands_landmarks[1]["lmList"][9]
    else:
        left_hand = hands_landmarks[1]["lmList"][9]
        right_hand = hands_landmarks[0]["lmList"][9]

    lx, ly = left_hand[1], left_hand[2]
    rx, ry = right_hand[1], right_hand[2]

    # Calculate midpoint between the two hands
    midpoint = ((lx + rx) // 2, (ly + ry) // 2)

    # Calculate angle using arctangent
    delta_y = ry - ly
    delta_x = rx - lx

    if delta_x == 0:
        return 0, midpoint

    angle_rad = math.atan2(delta_y, delta_x)
    angle_deg = math.degrees(angle_rad)

    # Clamp the angle between -90 and 90 degrees
    angle_deg = max(-90, min(90, angle_deg))

    return angle_deg, midpoint
