package org.blagodarie.ui.symptoms;

import androidx.annotation.NonNull;
import androidx.collection.LongSparseArray;

import org.blagodarie.ForbiddenException;
import org.blagodarie.db.UserSymptom;
import org.blagodarie.server.ServerApiExecutor;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Locale;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import static org.blagodarie.server.ServerConnector.JSON_TYPE;

public final class AddUserSymptomsExecutor
        implements ServerApiExecutor<AddUserSymptomsExecutor.ApiResult> {

    public static final class ApiResult
            extends ServerApiExecutor.ApiResult {

    }

    private static final String USER_SYMPTOM_JSON_PATTERN = "{\"user_symptom_id\":%d,\"symptom_id\":%d,\"timestamp\":%d,\"latitude\":%f,\"longitude\":%f}";

    @NonNull
    private final Long mUserId;

    @NonNull
    private final Collection<UserSymptom> mUserSymptoms = new ArrayList<>();

    @NonNull
    private final LongSparseArray<UserSymptom> mUserSymptomsById = new LongSparseArray<>();

    public AddUserSymptomsExecutor (
            @NonNull final Long userId,
            @NonNull final Collection<UserSymptom> userSymptoms
    ) {
        mUserId = userId;
        mUserSymptoms.addAll(userSymptoms);
        for (UserSymptom userSymptom : userSymptoms) {
            mUserSymptomsById.put(userSymptom.getId(), userSymptom);
        }
    }

    private String createJsonContent () {
        final StringBuilder content = new StringBuilder();
        content.append(String.format(Locale.ENGLISH, "{\"user_id\":%d,\"user_symptoms\":[", mUserId));

        boolean isFirst = true;
        for (UserSymptom userSymptom : mUserSymptoms) {
            if (!isFirst) {
                content.append(',');
            } else {
                isFirst = false;
            }
            content.append(
                    String.format(
                            Locale.ENGLISH,
                            USER_SYMPTOM_JSON_PATTERN,
                            userSymptom.getId(),
                            userSymptom.getSymptomId(),
                            (userSymptom.getTimestamp() / 1000),
                            userSymptom.getLatitude(),
                            userSymptom.getLongitude()));
        }
        content.append("]}");
        return content.toString();
    }

    @Override
    public ApiResult execute (
            @NonNull final String apiBaseUrl,
            @NonNull final OkHttpClient okHttpClient
    ) throws JSONException, IOException, ForbiddenException {
        final RequestBody body = RequestBody.create(JSON_TYPE, createJsonContent());
        final Request request = new Request.Builder()
                .url(apiBaseUrl + "addusersymptom")
                .post(body)
                .build();
        final Response response = okHttpClient.newCall(request).execute();
        if (response.code() == 200) {
            if (response.body() != null) {
                final String responseBody = response.body().string();
                final JSONObject responseJson = new JSONObject(responseBody);
                final JSONArray userSymptomsJson = responseJson.getJSONArray("user_symptoms");
                for (int i = 0; i < userSymptomsJson.length(); i++) {
                    final JSONObject element = userSymptomsJson.getJSONObject(i);
                    final long userSymptomId = element.getLong("user_symptom_id");
                    final long userSymptomServerId = element.getLong("user_symptom_server_id");
                    final UserSymptom userSymptom = mUserSymptomsById.get(userSymptomId);
                    if (userSymptom != null) {
                        userSymptom.setServerId(userSymptomServerId);
                    }
                }
            }
        } else if (response.code() == 403) {
            throw new ForbiddenException();
        }
        return new ApiResult();
    }


}
