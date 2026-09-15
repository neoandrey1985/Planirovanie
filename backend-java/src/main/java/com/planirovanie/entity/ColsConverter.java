package com.planirovanie.entity;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;

import java.util.ArrayList;
import java.util.List;

/** Persists a Kanban board's ordered list of columns (statuses) as a JSON array in a TEXT column. */
@Converter
public class ColsConverter implements AttributeConverter<List<String>, String> {
    private static final ObjectMapper M = new ObjectMapper();

    @Override
    public String convertToDatabaseColumn(List<String> cols) {
        try {
            return cols == null ? "[]" : M.writeValueAsString(cols);
        } catch (Exception e) {
            return "[]";
        }
    }

    @Override
    public List<String> convertToEntityAttribute(String s) {
        if (s == null || s.isBlank()) return new ArrayList<>();
        try {
            return M.readValue(s, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            return new ArrayList<>();
        }
    }
}
