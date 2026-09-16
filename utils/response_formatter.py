def format_chemical(chemical):

    uses = "\n".join(f"• {item}" for item in chemical.get("uses", []))
    hazards = "\n".join(f"• {item}" for item in chemical.get("hazards", []))
    ppe = "\n".join(f"• {item}" for item in chemical.get("ppe", []))

    aliases = chemical.get("aliases", [])
    aliases_text = ", ".join(aliases) if aliases else "None"

    ghs = "\n".join(f"• {item}" for item in chemical.get("ghs", []))

    return f"""
🧪 CHEMICAL INFORMATION
────────────────────────────────

🧪 Name              : {chemical['name']}
🧬 Formula           : {chemical['formula']}
📂 Category          : {chemical['category']}
🏷️ Aliases           : {aliases_text}

📝 Description
{chemical['description']}

🔬 Uses
{uses}

⚠ Hazards
{hazards}

🦺 PPE
{ppe}

📦 Storage
{chemical['storage']}

🚑 First Aid
{chemical['first_aid']}

♻ Disposal
{chemical['disposal']}

🌱 Green Alternative
{chemical['green_alternative']}

🌍 Environmental Impact
{chemical['environmental_impact']}

🚨 Signal Word
{chemical['signal_word']}

☣ GHS Symbols
{ghs}
"""


def format_green_chemistry(data):

    objectives = "\n".join(f"• {item}" for item in data["objectives"])
    benefits = "\n".join(f"• {item}" for item in data["benefits"])

    return f"""
🌱 GREEN CHEMISTRY
────────────────────────────────

📖 Definition
{data["definition"]}

🎯 Objectives
{objectives}

🌍 Benefits
{benefits}

💡 Example
{data["example"]}
"""


def format_lab_safety(data):

    rules = "\n".join(f"• {item}" for item in data["rules"])
    ppe = "\n".join(f"• {item}" for item in data["ppe"])
    emergency = "\n".join(f"• {item}" for item in data["emergency"])

    return f"""
🛡 LABORATORY SAFETY
────────────────────────────────

👨‍🔬 Basic Rules
{rules}

🦺 Required PPE
{ppe}

🚨 Emergency
{emergency}
"""
