"""Ubicación nacional argentina para SALVA."""

PROVINCES = [
    "Buenos Aires",
    "Ciudad Autónoma de Buenos Aires",
    "Catamarca",
    "Chaco",
    "Chubut",
    "Córdoba",
    "Corrientes",
    "Entre Ríos",
    "Formosa",
    "Jujuy",
    "La Pampa",
    "La Rioja",
    "Mendoza",
    "Misiones",
    "Neuquén",
    "Río Negro",
    "Salta",
    "San Juan",
    "San Luis",
    "Santa Cruz",
    "Santa Fe",
    "Santiago del Estero",
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur",
    "Tucumán",
]

LOCALITY_SUGGESTIONS: dict[str, list[str]] = {
    "Ciudad Autónoma de Buenos Aires": [
        "Ciudad Autónoma de Buenos Aires", "Palermo", "Recoleta", "Belgrano",
        "Caballito", "Almagro", "Villa Crespo", "San Telmo", "Puerto Madero",
    ],
    "Buenos Aires": [
        "La Plata", "Mar del Plata", "Bahía Blanca", "Quilmes", "San Isidro",
        "Tigre", "Lomas de Zamora", "Morón", "Pilar",
    ],
    "Córdoba": ["Córdoba", "Villa Carlos Paz", "Río Cuarto", "Alta Gracia"],
    "Santa Fe": ["Rosario", "Santa Fe", "Rafaela", "Venado Tuerto"],
    "Mendoza": ["Mendoza", "San Rafael", "Godoy Cruz", "Luján de Cuyo"],
    "Tucumán": ["San Miguel de Tucumán", "Yerba Buena", "Tafí Viejo"],
    "Salta": ["Salta", "San Lorenzo", "Cerrillos"],
    "Neuquén": ["Neuquén", "San Martín de los Andes", "Cipolletti"],
    "Río Negro": ["Bariloche", "Viedma", "General Roca"],
    "Chubut": ["Comodoro Rivadavia", "Trelew", "Puerto Madryn"],
    "Entre Ríos": ["Paraná", "Concordia", "Gualeguaychú"],
    "Misiones": ["Posadas", "Oberá", "Puerto Iguazú"],
    "Corrientes": ["Corrientes", "Goya", "Paso de los Libres"],
    "San Juan": ["San Juan", "Rawson", "Rivadavia"],
    "San Luis": ["San Luis", "Villa Mercedes", "Merlo"],
    "La Pampa": ["Santa Rosa", "General Pico"],
    "La Rioja": ["La Rioja", "Chilecito"],
    "Catamarca": ["San Fernando del Valle de Catamarca", "Andalgalá"],
    "Santiago del Estero": ["Santiago del Estero", "La Banda"],
    "Formosa": ["Formosa", "Clorinda"],
    "Jujuy": ["San Salvador de Jujuy", "Palpalá"],
    "Chaco": ["Resistencia", "Presidencia Roque Sáenz Peña"],
    "Santa Cruz": ["Río Gallegos", "Caleta Olivia", "El Calafate"],
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur": ["Ushuaia", "Río Grande"],
}


def locality_options(province: str) -> list[str]:
    return LOCALITY_SUGGESTIONS.get(province, [])


def location_summary(
    address: str,
    neighborhood: str,
    locality: str,
    province: str,
    apartment: str = "",
) -> str:
    parts = [p.strip() for p in [address, neighborhood, locality, province] if p and p.strip()]
    if apartment and apartment.strip():
        parts[0] = f"{parts[0]}, {apartment.strip()}" if parts else apartment.strip()
    return ", ".join(parts)


def legacy_location(booking: dict) -> str:
    if booking.get("province") or booking.get("locality"):
        return location_summary(
            booking.get("address") or booking.get("location", ""),
            booking.get("neighborhood", ""),
            booking.get("locality", ""),
            booking.get("province", ""),
            booking.get("apartment", ""),
        )
    loc = booking.get("location", "")
    hood = booking.get("neighborhood", "")
    return f"{loc}, {hood}" if loc and hood else (loc or hood or "—")
