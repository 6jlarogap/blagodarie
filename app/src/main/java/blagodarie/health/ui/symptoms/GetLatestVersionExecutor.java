package blagodarie.health.ui.symptoms;

import android.net.Uri;
import android.util.Log;

import androidx.annotation.NonNull;

import blagodarie.health.server.ServerApiExecutor;
import blagodarie.health.server.ServerApiResponse;
import blagodarie.health.server.ServerConnector;
import org.json.JSONObject;

import java.util.UUID;

final class GetLatestVersionExecutor {

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

        private final UUID mIncognitoPublicKey;

        private final Long mIncognitoPublicKeyTimestamp;

        private ApiResult (
                final boolean googlePlayUpdate,
                @NonNull final VersionName versionName,
                final int versionCode,
                @NonNull final Uri latestVersionUri,
                @NonNull final Uri playMarketUri,
                final UUID incognitoPublicKey,
                final Long incognitoPublicKeyTimestamp
        ) {
            mGooglePlayUpdate = googlePlayUpdate;
            mVersionName = versionName;
            mVersionCode = versionCode;
            mLatestVersionUri = latestVersionUri;
            mPlayMarketUri = playMarketUri;
            mIncognitoPublicKey = incognitoPublicKey;
            mIncognitoPublicKeyTimestamp = incognitoPublicKeyTimestamp;
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

        final UUID getIncognitoPublicKey () {
            return mIncognitoPublicKey;
        }

        final Long getIncognitoPublicKeyTimestamp () {
            return mIncognitoPublicKeyTimestamp;
        }

        @Override
        public String toString () {
            return "ApiResult{" +
                    "mGooglePlayUpdate=" + mGooglePlayUpdate +
                    ", mVersionName=" + mVersionName +
                    ", mVersionCode=" + mVersionCode +
                    ", mLatestVersionUri=" + mLatestVersionUri +
                    ", mPlayMarketUri=" + mPlayMarketUri +
                    ", mIncognitoPublicKey=" + mIncognitoPublicKey +
                    ", mIncognitoPublicKeyTimestamp=" + mIncognitoPublicKeyTimestamp +
                    '}';
        }
    }

    @NonNull
    private final UUID mIncognitoPrivateKey;

    GetLatestVersionExecutor (@NonNull final UUID incognitoPrivateKey) {
        mIncognitoPrivateKey = incognitoPrivateKey;
    }

    public ApiResult execute (@NonNull final ServerConnector serverConnector) throws Exception {
        Log.d(TAG, "execute");
        ApiResult apiResult = null;

        final ServerApiResponse serverApiResponse = serverConnector.sendRequestAndGetResponse("getlatestversion?incognito_private_key=" + mIncognitoPrivateKey.toString());
        Log.d(TAG, "serverApiResponse=" + serverApiResponse);

        if (serverApiResponse.getBody() != null) {
            final String responseBody = serverApiResponse.getBody();
            Log.d(TAG, "responseBody=" + responseBody);
            final JSONObject rootJSON = new JSONObject(responseBody);
            final boolean googlePlayUpdate = rootJSON.getBoolean("google_play_update");
            final int versionCode = rootJSON.getInt("version_code");
            final String versionNameString = rootJSON.getString("version_name");
            final VersionName versionName = new VersionName(versionNameString.replaceAll("-dbg", ""));
            final String url = rootJSON.getString("url");
            final String playMarketUri = rootJSON.getString("google_play_url");
            final String incognitoPublicKey = rootJSON.getString("incognito_public_key");
            final Long incognitoPublicKeyTimestamp = rootJSON.getLong("incognito_public_key_timestamp");
            apiResult = new ApiResult(
                    googlePlayUpdate,
                    versionName,
                    versionCode,
                    Uri.parse(url),
                    Uri.parse(playMarketUri),
                    UUID.fromString(incognitoPublicKey),
                    incognitoPublicKeyTimestamp
            );
        }
        return apiResult;
    }
}
