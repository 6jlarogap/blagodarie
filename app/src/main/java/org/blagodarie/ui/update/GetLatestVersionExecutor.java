package org.blagodarie.ui.update;

import android.net.Uri;
import android.util.Log;

import androidx.annotation.NonNull;

import org.blagodarie.server.ServerApiExecutor;
import org.json.JSONObject;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

final class GetLatestVersionExecutor
        implements ServerApiExecutor<GetLatestVersionExecutor.ApiResult> {

    private static final String TAG = GetLatestVersionExecutor.class.getSimpleName();

    static final class ApiResult
            extends ServerApiExecutor.ApiResult {

        private final boolean mGooglePlayUpdate;

        @NonNull
        private final VersionName mVersionName;

        private final int mVersionCode;

        @NonNull
        private final Uri mLatestVersionUri;

        @NonNull
        private final Uri mPlayMarketUri;

        private ApiResult (
                final boolean googlePlayUpdate,
                @NonNull final VersionName versionName,
                final int versionCode,
                @NonNull final Uri latestVersionUri,
                @NonNull final Uri playMarketUri
        ) {
            mGooglePlayUpdate = googlePlayUpdate;
            mVersionName = versionName;
            mVersionCode = versionCode;
            mLatestVersionUri = latestVersionUri;
            mPlayMarketUri = playMarketUri;
        }

        @NonNull
        final VersionName getVersionName () {
            return mVersionName;
        }

        final int getVersionCode () {
            return mVersionCode;
        }

        @NonNull
        final Uri getUri () {
            return mLatestVersionUri;
        }

        final boolean isGooglePlayUpdate () {
            return mGooglePlayUpdate;
        }

        @NonNull
        final Uri getPlayMarketUri () {
            return mPlayMarketUri;
        }

        @Override
        public String toString () {
            return "ApiResult{" +
                    "mGooglePlayUpdate=" + mGooglePlayUpdate +
                    ", mVersionName=" + mVersionName +
                    ", mVersionCode=" + mVersionCode +
                    ", mLatestVersionUri=" + mLatestVersionUri +
                    ", mPlayMarketUri=" + mPlayMarketUri +
                    '}';
        }
    }

    @Override
    public ApiResult execute (
            @NonNull final String apiBaseUrl,
            @NonNull final OkHttpClient okHttpClient
    ) throws Exception {
        Log.d(TAG, "execute");
        ApiResult apiResult = null;
        final Request request = new Request.Builder()
                .url(apiBaseUrl + "getlatestversion")
                .build();
        Log.d(TAG, "request=" + request);
        final Response response = okHttpClient.newCall(request).execute();
        Log.d(TAG, "response.code=" + response.code());
        if (response.body() != null) {
            final String responseBody = response.body().string();
            Log.d(TAG, "responseBody=" + responseBody);
            final JSONObject rootJSON = new JSONObject(responseBody);
            final boolean googlePlayUpdate = rootJSON.getBoolean("google_play_update");
            final int versionCode = rootJSON.getInt("version_code");
            final String versionNameString = rootJSON.getString("version_name");
            final VersionName versionName = new VersionName(versionNameString.replaceAll("-dbg", ""));
            final String url = rootJSON.getString("url");
            final String playMarketUri = rootJSON.getString("google_play_url");
            apiResult = new ApiResult(googlePlayUpdate, versionName, versionCode, Uri.parse(url), Uri.parse(playMarketUri));
        }
        return apiResult;
    }
}
