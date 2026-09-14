package com.planirovanie.service;

import org.springframework.stereotype.Component;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.security.SecureRandom;
import java.util.Base64;

/**
 * Password hashing with PBKDF2WithHmacSHA256 — JDK-only, no external dependency.
 * Stored format: {@code pbkdf2$<iterations>$<saltBase64>$<hashBase64>}.
 */
@Component
public class PasswordHasher {

    private static final int ITERATIONS = 120_000;
    private static final int KEY_LEN = 256;       // bits
    private static final int SALT_LEN = 16;       // bytes
    private static final SecureRandom RNG = new SecureRandom();

    public String hash(String password) {
        byte[] salt = new byte[SALT_LEN];
        RNG.nextBytes(salt);
        byte[] dk = pbkdf2(password.toCharArray(), salt, ITERATIONS, KEY_LEN);
        Base64.Encoder b64 = Base64.getEncoder();
        return "pbkdf2$" + ITERATIONS + "$" + b64.encodeToString(salt) + "$" + b64.encodeToString(dk);
    }

    public boolean verify(String password, String stored) {
        if (password == null || stored == null) return false;
        String[] parts = stored.split("\\$");
        if (parts.length != 4 || !"pbkdf2".equals(parts[0])) return false;
        try {
            int iterations = Integer.parseInt(parts[1]);
            byte[] salt = Base64.getDecoder().decode(parts[2]);
            byte[] expected = Base64.getDecoder().decode(parts[3]);
            byte[] actual = pbkdf2(password.toCharArray(), salt, iterations, expected.length * 8);
            return constantTimeEquals(expected, actual);
        } catch (RuntimeException ex) {
            return false;
        }
    }

    private static byte[] pbkdf2(char[] password, byte[] salt, int iterations, int keyLenBits) {
        try {
            SecretKeyFactory f = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
            return f.generateSecret(new PBEKeySpec(password, salt, iterations, keyLenBits)).getEncoded();
        } catch (Exception e) {
            throw new IllegalStateException("PBKDF2 failure", e);
        }
    }

    private static boolean constantTimeEquals(byte[] a, byte[] b) {
        if (a.length != b.length) return false;
        int r = 0;
        for (int i = 0; i < a.length; i++) r |= a[i] ^ b[i];
        return r == 0;
    }
}
