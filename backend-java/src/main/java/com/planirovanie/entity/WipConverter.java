package com.planirovanie.entity;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

import java.util.LinkedHashMap;
import java.util.Map;

/** Persists a Kanban board's per-column WIP limits (column -> limit) as a JSON object in a TEXT column. */
@Converter
public class WipConverter implements AttributeConverter<Map<String, Integer>, String> {
    private static final ObjectMapper M = new ObjectMapper();

    @Override
    public String convertToDatabaseColumn(Map<String, Integer> wip) {
        try {
            return (wip == null || wip.isEmpty()) ? null : M.writeValueAsString(wip);
        } catch (Exception e) {
            return null;
        }
    }

    @Override
    public Map<String, Integer> convertToEntityAttribute(String s) {
        if (s == null || s.isBlank()) return new LinkedHashMap<>();
        try {
            return M.readValue(s, new TypeReference<LinkedHashMap<String, Integer>>() {});
        } catch (Exception e) {
            return new LinkedHashMap<>();
        }
    }
}
