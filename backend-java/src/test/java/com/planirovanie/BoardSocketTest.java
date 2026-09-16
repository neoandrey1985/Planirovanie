package com.planirovanie;

import com.planirovanie.web.BoardSocketHandler;
import org.junit.jupiter.api.Test;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Unit-tests the whiteboard relay logic with mocked sessions (no network — the sandbox cannot
 * bind a real server port). Verifies presence (welcome/join/leave), broadcast to others, and
 * that a client does not receive an echo of its own message.
 */
class BoardSocketTest {

    private WebSocketSession fake(List<String> sink, String name) {
        WebSocketSession s = mock(WebSocketSession.class);
        when(s.isOpen()).thenReturn(true);
        Map<String, Object> attrs = new HashMap<>();
        if (name != null) attrs.put("name", name);
        when(s.getAttributes()).thenReturn(attrs);
        try {
            doAnswer(inv -> { sink.add(((TextMessage) inv.getArgument(0)).getPayload()); return null; })
                .when(s).sendMessage(any());
        } catch (Exception ignore) {}
        return s;
    }

    @Test
    void relaysOpsAndPresence() throws Exception {
        BoardSocketHandler h = new BoardSocketHandler();
        List<String> aMsgs = new ArrayList<>(), bMsgs = new ArrayList<>();
        WebSocketSession b = fake(bMsgs, "Bob");
        WebSocketSession a = fake(aMsgs, "Ann");

        h.afterConnectionEstablished(b);            // Bob connects -> gets welcome
        assertTrue(bMsgs.stream().anyMatch(m -> m.contains("\"type\":\"welcome\"")));

        h.afterConnectionEstablished(a);            // Ann connects -> Bob sees join
        assertTrue(bMsgs.stream().anyMatch(m -> m.contains("\"type\":\"join\"") && m.contains("Ann")));

        // Ann creates a sticky -> Bob receives it (stamped with from + Ann's name), Ann does NOT echo.
        h.handleTextMessage(a, new TextMessage("{\"type\":\"op\",\"op\":\"upsert\",\"item\":{\"id\":\"x1\",\"t\":\"sticky\"}}"));
        assertTrue(bMsgs.stream().anyMatch(m -> m.contains("\"op\"") && m.contains("x1") && m.contains("\"from\":") && m.contains("Ann")));
        assertFalse(aMsgs.stream().anyMatch(m -> m.contains("x1")), "sender must not receive its own op");

        // Cursor relay likewise reaches the other peer.
        h.handleTextMessage(a, new TextMessage("{\"type\":\"cursor\",\"x\":10,\"y\":20}"));
        assertTrue(bMsgs.stream().anyMatch(m -> m.contains("\"type\":\"cursor\"")));

        // Ann disconnects -> Bob sees leave.
        h.afterConnectionClosed(a, CloseStatus.NORMAL);
        assertTrue(bMsgs.stream().anyMatch(m -> m.contains("\"type\":\"leave\"")));
    }
}
