package blagodarie.health.server;

import androidx.annotation.Nullable;

public final class ServerApiResponse {

    private final int mCode;

    @Nullable
    private final String mBody;

    ServerApiResponse (
            final int code,
            @Nullable final String body
    ) {
        mCode = code;
        mBody = body;
    }

    public final int getCode () {
        return mCode;
    }

    @Nullable
    public final String getBody () {
        return mBody;
    }

    @Override
    public String toString () {
        return "ServerApiResponse{" +
                "mCode=" + mCode +
                ", mBody='" + mBody + '\'' +
                '}';
    }
}
