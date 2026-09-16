package com.planirovanie.config;

import com.planirovanie.service.AuthService;
import com.planirovanie.web.BoardSocketHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;
import org.springframework.web.socket.server.HandshakeInterceptor;

import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.Map;

/** Registers the whiteboard collaboration WebSocket at /ws/board and derives the display name
 *  from an optional bearer token (?token=) or an explicit ?name= query parameter. */
@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {
    private final BoardSocketHandler handler;
    private final AuthService auth;

    public WebSocketConfig(BoardSocketHandler handler, AuthService auth) {
        this.handler = handler; this.auth = auth;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(handler, "/ws/board").setAllowedOriginPatterns("*").addInterceptors(new HandshakeInterceptor() {
            @Override
            public boolean beforeHandshake(ServerHttpRequest req, ServerHttpResponse res, WebSocketHandler h, Map<String, Object> attrs) {
                String q = req.getURI().getQuery();
                String token = param(q, "token"), name = param(q, "name");
                if (token != null && !token.isBlank()) auth.resolve(token).ifPresent(us -> attrs.put("name", us.username));
                if (!attrs.containsKey("name") && name != null && !name.isBlank()) attrs.put("name", name);
                return true;
            }
            @Override
            public void afterHandshake(ServerHttpRequest req, ServerHttpResponse res, WebSocketHandler h, Exception ex) {}
        });
    }

    private static String param(String q, String key) {
        if (q == null) return null;
        for (String kv : q.split("&")) {
            int i = kv.indexOf('=');
            if (i > 0 && kv.substring(0, i).equals(key)) {
                try { return URLDecoder.decode(kv.substring(i + 1), StandardCharsets.UTF_8); }
                catch (Exception e) { return kv.substring(i + 1); }
            }
        }
        return null;
    }
}
