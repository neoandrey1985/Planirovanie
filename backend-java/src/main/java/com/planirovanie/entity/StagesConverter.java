package com.planirovanie.entity;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

import java.util.LinkedHashMap;
import java.util.Map;

/** Persists a task's manual stage dates (ba_s, ba_e, …, prod_e -> ISO date) as a JSON object in a TEXT column. */
@Converter
public class StagesConverter implements AttributeConverter<Map<String, String>, String> {
    private static final ObjectMapper M = new ObjectMapper();

    @Override
    public String convertToDatabaseColumn(Map<String, String> stages) {
        try {
            return (stages == null || stages.isEmpty()) ? null : M.writeValueAsString(stages);
        } catch (Exception e) {
            return null;
        }
    }

    @Override
    public Map<String, String> convertToEntityAttribute(String s) {
        if (s == null || s.isBlank()) return new LinkedHashMap<>();
        try {
            return M.readValue(s, new TypeReference<LinkedHashMap<String, String>>() {});
        } catch (Exception e) {
            return new LinkedHashMap<>();
        }
    }
}
