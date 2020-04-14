package org.blagodarie.server;

import androidx.annotation.NonNull;

import org.json.JSONException;

import java.io.IOException;

import okhttp3.OkHttpClient;

public interface ServerApiExecutor<T extends ServerApiExecutor.ApiResult> {
    abstract class ApiResult {
    }

    T execute (
            @NonNull final String apiBaseUrl,
            @NonNull final OkHttpClient okHttpClient
    ) throws Exception;
}
