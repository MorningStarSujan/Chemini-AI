"""
Knowledge Base
Stores all static AI knowledge for the Chemini AI.
"""

KNOWLEDGE = {
    "green chemistry": {
        "formatter": "green_chemistry",
        "keywords": [
            "green chemistry",
            "what is green chemistry",
            "define green chemistry",
            "explain green chemistry",
            "tell me about green chemistry",
            "green chemistry definition",
            "green chemistry meaning",
        ],
        "definition": "Green Chemistry is the design of chemical products and "
        "processes that reduce or eliminate hazardous substances.",
        "objectives": [
            "Reduce pollution",
            "Minimize hazardous chemicals",
            "Reduce chemical waste",
            "Improve laboratory safety",
            "Use renewable resources",
            "Increase energy efficiency",
        ],
        "benefits": [
            "Eco-friendly",
            "Safer experiments",
            "Cost-effective",
            "Sustainable development",
            "Lower environmental impact",
        ],
        "example": "Using ethanol instead of benzene whenever possible.",
    },
    "laboratory safety": {
        "formatter": "lab_safety",
        "keywords": [
            "laboratory safety",
            "lab safety",
            "chemical safety",
            "safety rules",
            "laboratory rules",
            "lab rules",
            "safety precautions",
        ],
        "rules": [
            "Always wear PPE.",
            "Read chemical labels carefully.",
            "Never mix unknown chemicals.",
            "Keep food away from the laboratory.",
            "Handle chemicals carefully.",
            "Keep the workplace clean.",
        ],
        "ppe": ["Safety Goggles", "Lab Coat", "Gloves", "Closed-Toe Shoes"],
        "emergency": [
            "Wash affected area immediately.",
            "Inform the laboratory supervisor.",
            "Follow emergency procedures.",
            "Use emergency equipment if necessary.",
        ],
    },
}
