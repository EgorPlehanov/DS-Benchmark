"""
Real-world application examples for the Dempster-Shafer package.

This module provides examples of real-world applications of Dempster-Shafer theory.
"""

from ..core import MassFunction, Frame

def medical_diagnosis_example():
    """
    Example of using Dempster-Shafer theory for medical diagnosis.
    
    This example models a simple medical diagnosis scenario with two symptoms
    and three possible diseases.
    
    Returns:
    --------
    dict
        Dictionary containing example mass functions and results.
    """
    # Create a frame of discernment with three diseases
    frame = Frame(['flu', 'cold', 'allergy'])
    
    # Evidence from symptom 1 (fever)
    # High fever suggests flu, mild fever suggests cold, no fever suggests allergy
    m1 = MassFunction({
        ('flu',): 0.7,
        ('cold',): 0.2,
        ('flu', 'cold'): 0.1
    }, frame)
    
    # Evidence from symptom 2 (sneezing)
    # Sneezing suggests cold or allergy
    m2 = MassFunction({
        ('cold',): 0.4,
        ('allergy',): 0.4,
        ('cold', 'allergy'): 0.2
    }, frame)
    
    # Combine evidence using Dempster's rule
    m_combined = m1.combine_conjunctive(m2)
    
    # Calculate belief and plausibility for each disease
    results = {}
    for disease in frame:
        disease_set = frozenset([disease])
        results[disease] = {
            'belief': m_combined.belief(disease_set),
            'plausibility': m_combined.plausibility(disease_set)
        }
    
    # Return results
    return {
        'symptom1_evidence': m1,
        'symptom2_evidence': m2,
        'combined_evidence': m_combined,
        'disease_results': results
    }

def sensor_fusion_example():
    """
    Example of using Dempster-Shafer theory for sensor fusion.
    
    This example models a simple sensor fusion scenario with three sensors
    detecting the presence of an object.
    
    Returns:
    --------
    dict
        Dictionary containing example mass functions and results.
    """
    from ..combination import combine_dubois_prade
    from ..discounting import discount_classical
    
    # Create a frame of discernment: object present or absent
    frame = Frame(['present', 'absent'])
    
    # Evidence from sensor 1 (80% reliable)
    m1_raw = MassFunction({
        ('present',): 0.75,
        ('absent',): 0.15,
        ('present', 'absent'): 0.1
    }, frame)
    
    # Discount sensor 1 based on reliability
    m1 = discount_classical(m1_raw, 0.8)
    
    # Evidence from sensor 2 (90% reliable)
    m2_raw = MassFunction({
        ('present',): 0.6,
        ('absent',): 0.3,
        ('present', 'absent'): 0.1
    }, frame)
    
    # Discount sensor 2 based on reliability
    m2 = discount_classical(m2_raw, 0.9)
    
    # Evidence from sensor 3 (70% reliable)
    m3_raw = MassFunction({
        ('present',): 0.4,
        ('absent',): 0.5,
        ('present', 'absent'): 0.1
    }, frame)
    
    # Discount sensor 3 based on reliability
    m3 = discount_classical(m3_raw, 0.7)
    
    # Combine evidence using Dempster's rule
    m_dempster = m1.combine_conjunctive(m2).combine_conjunctive(m3)
    
    # Combine evidence using Dubois & Prade's rule (handles conflict better)
    m_dp = combine_dubois_prade(combine_dubois_prade(m1, m2), m3)
    
    # Calculate belief and plausibility for object presence
    present_set = frozenset(['present'])
    
    # Return results
    return {
        'sensor1_evidence': m1,
        'sensor2_evidence': m2,
        'sensor3_evidence': m3,
        'combined_dempster': m_dempster,
        'combined_dubois_prade': m_dp,
        'presence_belief_dempster': m_dempster.belief(present_set),
        'presence_plausibility_dempster': m_dempster.plausibility(present_set),
        'presence_belief_dp': m_dp.belief(present_set),
        'presence_plausibility_dp': m_dp.plausibility(present_set)
    }

def run_all_examples():
    """
    Run all examples and print results.
    """
    # Run medical diagnosis example
    print("Medical Diagnosis Example:")
    results = medical_diagnosis_example()
    print("Combined evidence:")
    print(results['combined_evidence'])
    print("\nDisease results:")
    for disease, values in results['disease_results'].items():
        print(f"{disease}: Belief = {values['belief']:.4f}, Plausibility = {values['plausibility']:.4f}")
    print()
    
    # Run sensor fusion example
    print("Sensor Fusion Example:")
    results = sensor_fusion_example()
    print("Dempster's rule results:")
    print(f"Belief in presence: {results['presence_belief_dempster']:.4f}")
    print(f"Plausibility of presence: {results['presence_plausibility_dempster']:.4f}")
    print("\nDubois & Prade's rule results:")
    print(f"Belief in presence: {results['presence_belief_dp']:.4f}")
    print(f"Plausibility of presence: {results['presence_plausibility_dp']:.4f}")
    print()

if __name__ == "__main__":
    run_all_examples()
