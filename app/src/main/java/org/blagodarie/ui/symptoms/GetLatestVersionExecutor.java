package org.blagodarie.ui.symptoms;

import android.net.Uri;
import android.util.Log;

import androidx.annotation.NonNull;

import org.blagodarie.server.ServerApiExecutor;
import org.json.JSONObject;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

final class GetLatestVersionExecutor
        implements ServerApiExecutor<GetLatestVersionExecutor.ApiResult> {

    private static final String TAG = GetLatestVersionExecutor.class.getSimpleName();

    static final class ApiResult
            extends ServerApiExecutor.ApiResult {

        static final class VersionName {

            private static final String VERSION_NAME_PATTERN = "^\\d+\\.\\d+\\.\\d+$";
            final int MajorSegment;
            final int MiddleSegment;
            final int MinorSegment;

            VersionName (final String versionName) {
                final Pattern pattern = Pattern.compile(VERSION_NAME_PATTERN);
                final Matcher matcher = pattern.matcher(versionName);
                if (matcher.matches()) {
                    final String[] versionNameSegments = versionName.split("\\.");
                    MajorSegment = Integer.parseInt(versionNameSegments[0]);
                    MiddleSegment = Integer.parseInt(versionNameSegments[1]);
                    MinorSegment = Integer.parseInt(versionNameSegments[2]);
                } else {
                    throw new IllegalArgumentException("Incorrect version name string: " + versionName);
                }
            }

            @Override
            public String toString () {
                return MajorSegment + "." + MiddleSegment + "." + MinorSegment;
            }
        }

        private final boolean mGooglePlayUpdate;

        @NonNull
        private final VersionName mVersionName;

        private final int mVersionCode;

        @NonNull
        private final Uri mLatestVersionUri;

        @NonNull
        private final Uri mGooglePlayUri;

        private ApiResult (
                final boolean googlePlayUpdate,
                @NonNull final VersionName versionName,
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
        VersionName getVersionName () {
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

        boolean isGooglePlayUpdate () {
            return mGooglePlayUpdate;
        }

        @NonNull
        Uri getGooglePlayUri () {
            return mGooglePlayUri;
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
            final ApiResult.VersionName versionName = new ApiResult.VersionName(versionNameString);
            final String url = rootJSON.getString("url");
            final String googlePlayUrl = rootJSON.getString("google_play_url");
            apiResult = new ApiResult(googlePlayUpdate, versionName, versionCode, Uri.parse(url), Uri.parse(googlePlayUrl));
        }
        return apiResult;
    }
}
