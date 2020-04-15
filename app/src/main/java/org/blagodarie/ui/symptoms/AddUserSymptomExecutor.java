package org.blagodarie.ui.symptoms;

import androidx.annotation.NonNull;

import org.blagodarie.ForbiddenException;
import org.blagodarie.UserSymptom;
import org.blagodarie.server.ServerApiExecutor;
import org.json.JSONException;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Locale;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import static org.blagodarie.server.ServerConnector.JSON_TYPE;

final class AddUserSymptomExecutor
        implements ServerApiExecutor<AddUserSymptomExecutor.ApiResult> {

    static final class ApiResult
            extends ServerApiExecutor.ApiResult {

    }

    @NonNull
    private final Long mUserId;

    @NonNull
    private final Collection<UserSymptom> mUserSymptoms = new ArrayList<>();

    AddUserSymptomExecutor (
            @NonNull final Long userId,
            @NonNull final Collection<UserSymptom> userSymptoms
    ) {
        mUserId = userId;
        mUserSymptoms.addAll(userSymptoms);
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
            content.append(String.format(Locale.ENGLISH, "{\"symptom_id\":%d,\"timestamp\":%d,\"latitude\":%f,\"longitude\":%f}",
                    userSymptom.getSymptomId(), (userSymptom.getTimestamp() / 1000), userSymptom.getLatitude(), userSymptom.getLongitude()));
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
                boolean a = responseBody.isEmpty();
            }
        } else if (response.code() == 403) {
            throw new ForbiddenException();
        }
        return new ApiResult();
    }


}
