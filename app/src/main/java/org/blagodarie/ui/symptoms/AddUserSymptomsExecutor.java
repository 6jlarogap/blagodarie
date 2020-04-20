package org.blagodarie.ui.symptoms;

import androidx.annotation.NonNull;
import androidx.core.util.Pair;
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
import java.util.Random;

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
            Double latitude = userSymptom.getLatitude();
            Double longitude = userSymptom.getLongitude();

            if (latitude != null && longitude != null) {
                Pair<Double, Double> obfuscatedLocation = GpsObfuscator.obfuscate(
                        userSymptom.getLatitude(),
                        userSymptom.getLongitude(),
                        2);
                latitude = obfuscatedLocation.first;
                longitude = obfuscatedLocation.second;
            }
            content.append(String.format(Locale.ENGLISH, "{\"symptom_id\":%d,\"timestamp\":%d,\"latitude\":%f,\"longitude\":%f}",
                    userSymptom.getSymptomId(), (userSymptom.getTimestamp() / 1000), latitude, longitude));
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


    private static final class GpsObfuscator {
        private static final double MERIDIAN_LENGTH = 40008550D;
        private static final double EQUATOR_LENGTH = 40075696D;
        private static final double LATITUDE_DEGREE_LENGTH = 360D / MERIDIAN_LENGTH;
        private static final double LONGITUDE_EQUATOR_DEGREE_LENGTH = 360D / EQUATOR_LENGTH;

        private static final int MAX_DEVIATION = 300;

        private GpsObfuscator () {
        }

        @NonNull
        static Pair<Double, Double> obfuscate (
                @NonNull final Double latitude,
                @NonNull final Double longitude,
                final int count
        ) {
            Pair<Double, Double> obfLocation = new Pair<>(latitude, longitude);
            for (int i = 0; i < count; i++) {
                if (obfLocation.first != null && obfLocation.second != null) {
                    obfLocation = obfuscate(obfLocation.first, obfLocation.second);
                }
            }
            return obfLocation;
        }

        @NonNull
        static Pair<Double, Double> obfuscate (
                @NonNull final Double latitude,
                @NonNull final Double longitude
        ) {
            final Random random = new Random();
            double obfuscatedLatitude = latitude;
            double latitudeDeviationInMeters = random.nextInt(MAX_DEVIATION + 1);
            double latitudeDeviationInDegrees = latitudeDeviationInMeters * LATITUDE_DEGREE_LENGTH;
            if (random.nextBoolean()) {
                obfuscatedLatitude += latitudeDeviationInDegrees;
            } else {
                obfuscatedLatitude -= latitudeDeviationInDegrees;
            }

            double LONGITUDE_LOCAL_DEGREE_LENGTH = LONGITUDE_EQUATOR_DEGREE_LENGTH * Math.cos(obfuscatedLatitude);

            int maxDev = (int) Math.sqrt((MAX_DEVIATION * MAX_DEVIATION) - (latitudeDeviationInMeters * latitudeDeviationInMeters));
            double obfuscatedLongitude = longitude;
            int longitudeDeviationInMeters = random.nextInt(maxDev + 1);
            double longitudeDeviationInDegrees = longitudeDeviationInMeters * LONGITUDE_LOCAL_DEGREE_LENGTH;
            if (random.nextBoolean()) {
                obfuscatedLongitude += longitudeDeviationInDegrees;
            } else {
                obfuscatedLongitude -= longitudeDeviationInDegrees;
            }

            return new Pair<>(obfuscatedLatitude, obfuscatedLongitude);
        }
    }
}
