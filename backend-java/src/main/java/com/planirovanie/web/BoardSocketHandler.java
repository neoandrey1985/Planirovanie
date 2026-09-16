package com.planirovanie.web;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Real-time collaboration relay for the whiteboard: a single shared room that broadcasts
 * every message (board operations + live cursors) to all other connected clients, and
 * announces join/leave for presence. Authoritative data is still persisted via /api/state.
 */
@Component
public class BoardSocketHandler extends TextWebSocketHandler {
    private static final String[] COLORS = {"#2D5BE3","#1F9D6B","#D24545","#C98A00","#8A5BD6","#0EA5A5","#E5588F","#7A8AA0"};
    private final Map<String, WebSocketSession> sessions = new ConcurrentHashMap<>();
    private final Map<String, String[]> peers = new ConcurrentHashMap<>(); // id -> [name, color]
    private final ObjectMapper M = new ObjectMapper();
    private final AtomicInteger seq = new AtomicInteger();

    @Override
    public void afterConnectionEstablished(WebSocketSession s) {
        String id = "u" + Long.toString(System.nanoTime(), 36) + seq.incrementAndGet();
        String color = COLORS[Math.abs(id.hashCode()) % COLORS.length];
        Object nm = s.getAttributes().get("name");
        String name = nm != null ? nm.toString() : "Гость";
        s.getAttributes().put("cid", id);
        sessions.put(id, s);
        peers.put(id, new String[]{name, color});
        ObjectNode w = M.createObjectNode();
        w.put("type", "welcome"); w.put("id", id); w.put("color", color);
        ArrayNode arr = w.putArray("peers");
        peers.forEach((k, p) -> { if (!k.equals(id)) { ObjectNode o = arr.addObject(); o.put("id", k); o.put("name", p[0]); o.put("color", p[1]); } });
        send(s, w.toString());
        ObjectNode j = M.createObjectNode();
        j.put("type", "join"); j.put("id", id); j.put("name", name); j.put("color", color);
        broadcast(j.toString(), id);
    }

    @Override
    public void handleTextMessage(WebSocketSession s, TextMessage message) {
        String cid = (String) s.getAttributes().get("cid");
        if (cid == null) return;
        try {
            JsonNode node = M.readTree(message.getPayload());
            if (!node.isObject()) return;
            ObjectNode o = (ObjectNode) node;
            String type = o.path("type").asText("");
            String[] p = peers.get(cid);
            if ("hello".equals(type) && o.hasNonNull("name") && p != null) p[0] = o.get("name").asText();
            o.put("from", cid);
            if (p != null) { o.put("color", p[1]); if (!o.hasNonNull("name")) o.put("name", p[0]); }
            broadcast(o.toString(), cid);
        } catch (Exception ignore) {}
    }

    @Override
    public void afterConnectionClosed(WebSocketSession s, CloseStatus status) {
        String cid = (String) s.getAttributes().get("cid");
        if (cid == null) return;
        sessions.remove(cid);
        peers.remove(cid);
        ObjectNode l = M.createObjectNode();
        l.put("type", "leave"); l.put("id", cid);
        broadcast(l.toString(), cid);
    }

    private void broadcast(String msg, String exceptId) {
        sessions.forEach((id, sess) -> { if (!id.equals(exceptId)) send(sess, msg); });
    }

    private void send(WebSocketSession s, String msg) {
        if (s == null || !s.isOpen()) return;
        try { synchronized (s) { s.sendMessage(new TextMessage(msg)); } } catch (Exception ignore) {}
    }
}
