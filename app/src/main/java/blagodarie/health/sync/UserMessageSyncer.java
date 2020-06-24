package blagodarie.health.sync;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.util.Pair;

import blagodarie.health.Repository;
import blagodarie.health.UnauthorizedException;
import blagodarie.health.database.UserMessage;
import blagodarie.health.server.ServerApiResponse;
import blagodarie.health.server.ServerConnector;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Random;
import java.util.UUID;

public final class UserMessageSyncer {

    private static final String TAG = UserMessageSyncer.class.getSimpleName();

    /**
     * Время подтверждения сообщения в миллисекундах. В течении этого времени сообщение можно отменить.
     */
    public static final long USER_MESSAGE_CONFIRMATION_TIME = 3000L;

    private static final String USER_MESSAGE_JSON_PATTERN = "{\"symptom_id\":%s,\"message_id\":%s,\"timestamp\":%d,\"timezone\":\"%s\",\"latitude\":%f,\"longitude\":%f}";// TODO: 24.06.2020 после перехода убрать symptom_id

    private static volatile UserMessageSyncer INSTANCE;

    private UserMessageSyncer () {
    }

    @NonNull
    static UserMessageSyncer getInstance () {
        Log.d(TAG, "getInstance");
        synchronized (UserMessageSyncer.class) {
            if (INSTANCE == null) {
                INSTANCE = new UserMessageSyncer();
            }
        }
        return INSTANCE;
    }

    final synchronized void sync (
            @NonNull final UUID incognitoId,
            @Nullable final String authToken,
            @NonNull final ServerConnector serverConnector,
            @NonNull final Repository repository
    ) throws IOException, UnauthorizedException {
        Log.d(TAG, "sync");
        final List<UserMessage> notSyncedUserMessages = repository.getNotSyncedUserMessages(incognitoId);
        Log.d(TAG, "notSyncedUserMessages.size=" + notSyncedUserMessages.size());
        final List<UserMessage> confirmedUserMessages = excludeUnconfirmed(notSyncedUserMessages);
        Log.d(TAG, "confirmedUserMessages.size=" + confirmedUserMessages.size());
        if (confirmedUserMessages.size() > 0) {
            final String content = createJsonContent(incognitoId, confirmedUserMessages);
            Log.d(TAG, "content=" + content);

            final ServerApiResponse serverApiResponse = serverConnector.sendRequestAndGetResponse("addincognitosymptom", content);
            Log.d(TAG, "serverApiResponse=" + serverApiResponse);

            if (serverApiResponse.getCode() == 200) {
                repository.deleteUserMessages(confirmedUserMessages);
            } else if (serverApiResponse.getCode() == 401) {
                throw new UnauthorizedException();
            }
        }
    }

    private List<UserMessage> excludeUnconfirmed (@NonNull final List<UserMessage> userMessages){
        final List<UserMessage> confirmentUserMessages = new ArrayList<>();
        for (UserMessage userMessage : userMessages){
            final long howLongAgo = System.currentTimeMillis() - userMessage.getTimestamp().getTime();
            if (howLongAgo > UserMessageSyncer.USER_MESSAGE_CONFIRMATION_TIME) {
                confirmentUserMessages.add(userMessage);
            }
        }
        return confirmentUserMessages;
    }

    private String createJsonContent (
            @NonNull final UUID incognitoId,
            @NonNull final Collection<UserMessage> userMessages
    ) {
        final StringBuilder content = new StringBuilder();
        content.append(String.format(Locale.ENGLISH, "{\"incognito_id\":\"%s\",\"user_symptoms\":[", incognitoId));

        boolean isFirst = true;
        for (UserMessage userMessage : userMessages) {
            if (!isFirst) {
                content.append(',');
            } else {
                isFirst = false;
            }
            Double latitude = userMessage.getLatitude();
            Double longitude = userMessage.getLongitude();

            if (latitude != null && longitude != null) {
                Pair<Double, Double> obfuscatedLocation = LocationObfuscator.obfuscate(
                        userMessage.getLatitude(),
                        userMessage.getLongitude(),
                        2);
                latitude = obfuscatedLocation.first;
                longitude = obfuscatedLocation.second;
            }
            final SimpleDateFormat sdfTimeZone = new SimpleDateFormat("Z", Locale.ENGLISH);
            content.append(
                    String.format(
                            Locale.ENGLISH,
                            USER_MESSAGE_JSON_PATTERN,
                            userMessage.getMessageId(),
                            userMessage.getMessageId(),
                            (userMessage.getTimestamp().getTime() / 1000),
                            sdfTimeZone.format(userMessage.getTimestamp()),
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
