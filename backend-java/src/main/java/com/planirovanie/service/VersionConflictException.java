package com.planirovanie.service;

/** Thrown when a PUT /api/state carries a baseVersion that no longer matches the stored version. */
public class VersionConflictException extends RuntimeException {
    public final long currentVersion;

    public VersionConflictException(long currentVersion) {
        super("version conflict; current=" + currentVersion);
        this.currentVersion = currentVersion;
    }
}
