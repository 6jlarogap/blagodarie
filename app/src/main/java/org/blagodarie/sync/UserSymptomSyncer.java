package org.blagodarie.sync;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.collection.LongSparseArray;
import androidx.core.util.Pair;

import org.blagodarie.UnauthorizedException;
import org.blagodarie.db.UserSymptom;
import org.blagodarie.db.UserSymptomDao;
import org.blagodarie.server.ServerConnector;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Random;

import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import static org.blagodarie.server.ServerConnector.JSON_TYPE;

final class UserSymptomSyncer {

    private static final String TAG = UserSymptomSyncer.class.getSimpleName();

    private static final String USER_SYMPTOM_JSON_PATTERN = "{\"user_symptom_id\":%d,\"symptom_id\":%d,\"timestamp\":%d,\"latitude\":%f,\"longitude\":%f}";

    private static volatile UserSymptomSyncer INSTANCE;

    private UserSymptomSyncer () {
    }

    @NonNull
    static UserSymptomSyncer getInstance () {
        synchronized (UserSymptomSyncer.class) {
            if (INSTANCE == null) {
                INSTANCE = new UserSymptomSyncer();
            }
        }
        return INSTANCE;
    }

    final synchronized void sync (
            @NonNull final Long userId,
            @NonNull final String authToken,
            @NonNull final String apiBaseUrl,
            @NonNull final UserSymptomDao userSymptomDao
    ) throws IOException, JSONException, UnauthorizedException {
        final List<UserSymptom> notSyncedUserSymtpoms = userSymptomDao.getNotSynced(userId);
        if (notSyncedUserSymtpoms.size() > 0) {
            final LongSparseArray<UserSymptom> mUserSymptomsById = new LongSparseArray<>();
            for (UserSymptom userSymptom : notSyncedUserSymtpoms) {
                assert userSymptom.getId() != null;
                mUserSymptomsById.put(userSymptom.getId(), userSymptom);
            }
            final String content = createJsonContent(userId, notSyncedUserSymtpoms);
            final Request request = createRequest(apiBaseUrl, authToken, content);
            final Response response = ServerConnector.sendRequestAndGetRespone(request);

            Log.d(TAG, "response.code=" + response.code());
            if (response.code() == 200) {
                if (response.body() != null) {
                    final String responseBody = response.body().string();
                    Log.d(TAG, "responseBody=" + responseBody);
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
                    userSymptomDao.update(notSyncedUserSymtpoms);
                }
            } else if (response.code() == 401) {
                throw new UnauthorizedException();
            }
        }
    }

    private Request createRequest (
            @NonNull final String apiBaseUrl,
            @NonNull final String authToken,
            @NonNull final String content
    ) {
        final RequestBody body = RequestBody.create(JSON_TYPE, content);
        return new Request.Builder().
                url(apiBaseUrl + "addusersymptom").
                post(body).
                header("Authorization", String.format("Token %s", authToken)).
                build();
    }

    private String createJsonContent (
            @NonNull final Long userId,
            @NonNull final Collection<UserSymptom> userSymptoms
    ) {
        final StringBuilder content = new StringBuilder();
        content.append(String.format(Locale.ENGLISH, "{\"user_id\":%d,\"user_symptoms\":[", userId));

        boolean isFirst = true;
        for (UserSymptom userSymptom : userSymptoms) {
            if (!isFirst) {
                content.append(',');
            } else {
                isFirst = false;
            }
            Double latitude = userSymptom.getLatitude();
            Double longitude = userSymptom.getLongitude();

            if (latitude != null && longitude != null) {
                Pair<Double, Double> obfuscatedLocation = LocationObfuscator.obfuscate(
                        userSymptom.getLatitude(),
                        userSymptom.getLongitude(),
                        2);
                latitude = obfuscatedLocation.first;
                longitude = obfuscatedLocation.second;
            }
            content.append(String.format(Locale.ENGLISH,
                    USER_SYMPTOM_JSON_PATTERN,
                    userSymptom.getId(),
                    userSymptom.getSymptomId(),
                    (userSymptom.getTimestamp() / 1000),
                    latitude,
                    longitude));
        }
        content.append("]}");
        return content.toString();
    }

    private static final class LocationObfuscator {
        /**
         * Длина меридиана в метрах.
         *
         * @link https://ru.wikipedia.org/wiki/%D0%9C%D0%B5%D1%80%D0%B8%D0%B4%D0%B8%D0%B0%D0%BD#%D0%93%D0%B5%D0%BE%D0%B3%D1%80%D0%B0%D1%84%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B9_%D0%BC%D0%B5%D1%80%D0%B8%D0%B4%D0%B8%D0%B0%D0%BD
         */
        private static final double MERIDIAN_LENGTH = 20004274D;

        /**
         * Длина экватора в метрах.
         */
        private static final double EQUATOR_LENGTH = 40075696D;

        /**
         * Количество градусов в одном метре широты.
         */
        private static final double LATITUDE_DEGREE_LENGTH = 180D / MERIDIAN_LENGTH;

        /**
         * Количество градусов в одном метре долготы на экваторе.
         */
        private static final double LONGITUDE_EQUATOR_DEGREE_LENGTH = 360D / EQUATOR_LENGTH;

        /**
         * Максимальное отклонение в метрах.
         */
        private static final int MAX_DEVIATION = 300;

        private LocationObfuscator () {
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

            final double LONGITUDE_LOCAL_DEGREE_LENGTH = LONGITUDE_EQUATOR_DEGREE_LENGTH * Math.cos(obfuscatedLatitude);

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
