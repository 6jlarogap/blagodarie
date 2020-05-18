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

        private final boolean mGooglePlayUpdate;

        @NonNull
        private final String mVersionName;

        private final int mVersionCode;

        @NonNull
        private final Uri mLatestVersionUri;

        @NonNull
        private final Uri mGooglePlayUri;

        private ApiResult (
                final boolean googlePlayUpdate,
                @NonNull final String versionName,
                final int versionCode,
                @NonNull final Uri latestVersionUri,
                @NonNull final Uri googlePlayUri) {
            mGooglePlayUpdate = googlePlayUpdate;
            mVersionName = versionName;
            mVersionCode = versionCode;
            mLatestVersionUri = latestVersionUri;
            mGooglePlayUri = googlePlayUri;
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

        public boolean isGooglePlayUpdate () {
            return mGooglePlayUpdate;
        }

        @NonNull
        public Uri getGooglePlayUri () {
            return mGooglePlayUri;
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
            final boolean googlePlayUpdate = rootJSON.getBoolean("google_play_update");
            final int versionCode = 100500;//rootJSON.getInt("version_code");
            final String versionName = rootJSON.getString("version_name");
            final String url = rootJSON.getString("url");
            final String googlePlayUrl = rootJSON.getString("google_play_url");
            apiResult = new ApiResult(googlePlayUpdate, versionName, versionCode, Uri.parse(url), Uri.parse(googlePlayUrl));
        }
        return apiResult;
    }
}
