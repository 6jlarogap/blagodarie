package org.blagodarie.ui.symptoms;

import android.net.Uri;

import androidx.annotation.NonNull;

import org.blagodarie.server.ServerApiExecutor;
import org.json.JSONObject;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

class GetLatestVersionExecutor
        implements ServerApiExecutor<GetLatestVersionExecutor.ApiResult> {

    static final class ApiResult
            extends ServerApiExecutor.ApiResult {

        @NonNull
        private final String mVersionName;

        @NonNull
        private final Integer mVersionCode;

        @NonNull
        private final Uri mLatestVersionUri;

        private ApiResult (
                @NonNull final String versionName,
                @NonNull final Integer versionCode,
                @NonNull final Uri latestVersionUri) {
            this.mVersionName = versionName;
            this.mVersionCode = versionCode;
            this.mLatestVersionUri = latestVersionUri;
        }

        @NonNull
        String getVersionName () {
            return mVersionName;
        }

        @NonNull
        Integer getVersionCode () {
            return mVersionCode;
        }

        @NonNull
        Uri getUri () {
            return mLatestVersionUri;
        }
    }

    @Override
    public ApiResult execute (
            @NonNull final String apiBaseUrl,
            @NonNull final OkHttpClient okHttpClient
    ) throws Exception {
        ApiResult apiResult = null;
        final Request request = new Request.Builder()
                .url(apiBaseUrl + "getlatestversion")
                .build();
        final Response response = okHttpClient.newCall(request).execute();
        if (response.body() != null) {
            final String responseBody = response.body().string();
            final JSONObject rootJSON = new JSONObject(responseBody);
            int versionCode = rootJSON.getInt("version_code");
            String versionName = rootJSON.getString("version_name");
            String url = rootJSON.getString("url");
            apiResult = new ApiResult(versionName, versionCode, Uri.parse(url));
        }
        return apiResult;
    }
}
