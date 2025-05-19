import { useState, useEffect } from "react";

export default function useCityAutocomplete(query: string) {
    const [suggestions, setSuggestions] = useState<{ city: string, country: string }[]>([]);

    useEffect(() => {
        if (!query) return;

        const fetchCities = async () => {
            const res = await fetch(`https://wft-geo-db.p.rapidapi.com/v1/geo/cities?namePrefix=${query}&limit=5&sort=-population`, {
                method: 'GET',
                headers: {
                    'X-RapidAPI-Key': '85b216a1e6msheb06e7872dbd8a3p1d9a9ajsnfb4ec32c0c29',
                    'X-RapidAPI-Host': 'wft-geo-db.p.rapidapi.com'
                }
            });

            const data = await res.json();
            setSuggestions(
                data.data.map((item: any) => ({
                    city: item.name,
                    country: item.country
                }))
            );
        };

        fetchCities();
    }, [query]);

    return suggestions;
}
