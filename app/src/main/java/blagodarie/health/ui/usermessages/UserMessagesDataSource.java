package blagodarie.health.ui.usermessages;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.paging.DataSource;
import androidx.paging.PositionalDataSource;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

import blagodarie.health.server.ServerApiResponse;
import blagodarie.health.server.ServerConnector;

public final class UserMessagesDataSource
        extends PositionalDataSource<Date> {
    private static final String TAG = UserMessagesDataSource.class.getSimpleName();

    @NonNull
    private final UUID mIncognitoPublicKey;

    private final long mMessageId;

    @NonNull
    final ServerConnector mServerConnector;

    UserMessagesDataSource (
            @NonNull final UUID incognitoPublicKey,
            final long messageId,
            @NonNull final ServerConnector serverConnector
    ) {
        Log.d(TAG, "OperationDataSource");
        mIncognitoPublicKey = incognitoPublicKey;
        mMessageId = messageId;
        mServerConnector = serverConnector;
    }

    @Override
    public void loadInitial (@NonNull LoadInitialParams params, @NonNull LoadInitialCallback<Date> callback) {
        Log.d(TAG, "loadInitial from=" + params.requestedStartPosition + ", pageSize=" + params.pageSize);
        final String content = String.format(Locale.ENGLISH, "{\"incognito_id\":\"%s\",\"message_type_id\":%d,\"from\":%d,\"count\":%d}", mIncognitoPublicKey.toString(), mMessageId, params.requestedStartPosition, params.pageSize);
        try {
            final ServerApiResponse serverApiResponse = mServerConnector.sendRequestAndGetResponse("/getincognitomessages", content);
            if (serverApiResponse.getCode() == 200) {
                if (serverApiResponse.getBody() != null) {
                    final String responseBody = serverApiResponse.getBody();
                    Log.d(TAG, "responseBody=" + responseBody);
                    try {
                        final JSONArray jsonOperations = new JSONObject(responseBody).getJSONArray("user_messages");
                        final List<Date> messages = new ArrayList<>();
                        for (int i = 0; i < jsonOperations.length(); i++) {
                            final JSONObject operationJsonObject = jsonOperations.getJSONObject(i);
                            final Date timestamp = new Date(operationJsonObject.getLong("timestamp") * 1000);
                            messages.add(timestamp);
                        }
                        callback.onResult(messages, 0);
                    } catch (JSONException e) {
                        e.printStackTrace();
                    }
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void loadRange (@NonNull LoadRangeParams params, @NonNull LoadRangeCallback<Date> callback) {
        Log.d(TAG, "loadRange startPosition=" + params.startPosition + ", loadSize=" + params.loadSize);
        final String content = String.format(Locale.ENGLISH, "{\"incognito_id\":\"%s\",\"message_type_id\":%d,\"from\":%d,\"count\":%d}", mIncognitoPublicKey.toString(), mMessageId, params.startPosition, params.loadSize);
        try {
            final ServerApiResponse serverApiResponse = mServerConnector.sendRequestAndGetResponse("/getincognitomessages", content);
            if (serverApiResponse.getCode() == 200) {
                if (serverApiResponse.getBody() != null) {
                    final String responseBody = serverApiResponse.getBody();
                    Log.d(TAG, "responseBody=" + responseBody);
                    try {
                        final JSONArray jsonOperations = new JSONObject(responseBody).getJSONArray("user_messages");
                        final List<Date> messages = new ArrayList<>();
                        for (int i = 0; i < jsonOperations.length(); i++) {
                            final JSONObject operationJsonObject = jsonOperations.getJSONObject(i);
                            final Date timestamp = new Date(operationJsonObject.getLong("timestamp") * 1000);
                            messages.add(timestamp);
                        }
                        callback.onResult(messages);
                    } catch (JSONException e) {
                        e.printStackTrace();
                    }
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    static class OperationsDataSourceFactory
            extends Factory<Integer, Date> {

        @NonNull
        private final UUID mIncognitoPublicKey;

        private final long mMessageId;

        @NonNull
        final ServerConnector mServerConnector;

        OperationsDataSourceFactory (
                @NonNull final UUID incognitoPublicKey,
                final long messageId,
                @NonNull final ServerConnector serverConnector
        ) {
            mIncognitoPublicKey = incognitoPublicKey;
            mMessageId = messageId;
            mServerConnector = serverConnector;
        }

        @Override
        public DataSource<Integer, Date> create () {
            return new UserMessagesDataSource(mIncognitoPublicKey, mMessageId, mServerConnector);
        }

    }
}
