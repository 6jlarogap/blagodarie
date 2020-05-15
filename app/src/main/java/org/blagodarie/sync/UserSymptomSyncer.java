package org.blagodarie.sync;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.util.Pair;

import org.blagodarie.Repository;
import org.blagodarie.UnauthorizedException;
import org.blagodarie.server.ServerConnector;
import org.blagodatie.database.UserSymptom;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Random;
import java.util.UUID;

import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import static org.blagodarie.server.ServerConnector.JSON_TYPE;

public final class UserSymptomSyncer {

    private static final String TAG = UserSymptomSyncer.class.getSimpleName();

    public static final long USER_SYMPTOM_CONFIRMATION_TIME = 30000L;

    private static final String USER_SYMPTOM_JSON_PATTERN = "{\"symptom_id\":%s,\"timestamp\":%d,\"timezone\":\"%s\",\"latitude\":%f,\"longitude\":%f}";

    private static volatile UserSymptomSyncer INSTANCE;

    private UserSymptomSyncer () {
    }

    @NonNull
    static UserSymptomSyncer getInstance () {
        Log.d(TAG, "getInstance");
        synchronized (UserSymptomSyncer.class) {
            if (INSTANCE == null) {
                INSTANCE = new UserSymptomSyncer();
            }
        }
        return INSTANCE;
    }

    final synchronized void sync (
            @NonNull final UUID incognitoId,
            @Nullable final String authToken,
            @NonNull final String apiBaseUrl,
            @NonNull final Repository repository
    ) throws IOException, UnauthorizedException {
        Log.d(TAG, "sync");
        final List<UserSymptom> notSyncedUserSymtpoms = repository.getNotSyncedUserSymptoms(incognitoId);
        Log.d(TAG, "notSyncedUserSymtpoms.size=" + notSyncedUserSymtpoms.size());
        final List<UserSymptom> confirmedUserSymptoms = excludeUnconfirmed(notSyncedUserSymtpoms);
        Log.d(TAG, "confirmedUserSymptoms.size=" + confirmedUserSymptoms.size());
        if (confirmedUserSymptoms.size() > 0) {
            final String content = createJsonContent(incognitoId, confirmedUserSymptoms);
            Log.d(TAG, "content=" + content);

            final Request request = createRequest(apiBaseUrl, authToken, content);
            Log.d(TAG, "request=" + request);

            final Response response = ServerConnector.sendRequestAndGetRespone(request);
            Log.d(TAG, "response.code=" + response.code());

            if (response.code() == 200) {
                repository.deleteUserSymptoms(confirmedUserSymptoms);
            } else if (response.code() == 401) {
                throw new UnauthorizedException();
            }
        }
    }

    private List<UserSymptom> excludeUnconfirmed (@NonNull final List<UserSymptom> userSymptoms){
        final List<UserSymptom> confirmentUserSymptoms = new ArrayList<>();
        for (UserSymptom userSymptom : userSymptoms){
            final long howLongAgo = System.currentTimeMillis() - userSymptom.getTimestamp().getTime();
            if (howLongAgo > UserSymptomSyncer.USER_SYMPTOM_CONFIRMATION_TIME) {
                confirmentUserSymptoms.add(userSymptom);
            }
        }
        return confirmentUserSymptoms;
    }

    private Request createRequest (
            @NonNull final String apiBaseUrl,
            @Nullable final String authToken,
            @NonNull final String content
    ) {
        final RequestBody body = RequestBody.create(JSON_TYPE, content);
        final Request.Builder requestBuilder = new Request.Builder();
        if (authToken != null) {
            requestBuilder.url(apiBaseUrl + "add_user_symptom");
            requestBuilder.header("Authorization", String.format("Token %s", authToken));
        } else {
            requestBuilder.url(apiBaseUrl + "addincognitosymptom");
        }
        requestBuilder.post(body);
        return requestBuilder.build();
    }

    private String createJsonContent (
            @NonNull final UUID incognitoId,
            @NonNull final Collection<UserSymptom> userSymptoms
    ) {
        final StringBuilder content = new StringBuilder();
        content.append(String.format(Locale.ENGLISH, "{\"incognito_id\":\"%s\",\"user_symptoms\":[", incognitoId));

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
            final SimpleDateFormat sdfTimeZone = new SimpleDateFormat("Z", Locale.ENGLISH);
            content.append(
                    String.format(
                            Locale.ENGLISH,
                            USER_SYMPTOM_JSON_PATTERN,
                            userSymptom.getSymptomId(),
                            (userSymptom.getTimestamp().getTime() / 1000),
                            sdfTimeZone.format(userSymptom.getTimestamp()),
                            latitude,
                            longitude
                    )
            );
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
