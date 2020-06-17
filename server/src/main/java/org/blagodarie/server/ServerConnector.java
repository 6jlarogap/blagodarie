package org.blagodarie.server;

import android.annotation.SuppressLint;
import android.content.Context;

import androidx.annotation.NonNull;

import java.io.IOException;
import java.security.cert.CertificateException;
import java.util.concurrent.TimeUnit;

import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSession;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class ServerConnector {

    public static final MediaType JSON_TYPE = MediaType.parse("application/json; charset=utf-8");

    @NonNull
    private final String mApiBaseUrl;

    public ServerConnector (@NonNull final Context context) {
        mApiBaseUrl = context.getString(R.string.base_api_url);
    }

    @NonNull
    private static OkHttpClient generateDefaultOkHttp () {
        final OkHttpClient.Builder builder = new OkHttpClient.Builder();
        try {
            // Create a trust manager that does not validate certificate chains
            final TrustManager[] trustAllCerts = new TrustManager[]{
                    new X509TrustManager() {
                        @SuppressLint("TrustAllX509TrustManager")
                        @Override
                        public void checkClientTrusted (java.security.cert.X509Certificate[] chain, String authType) throws CertificateException {
                        }

                        @SuppressLint("TrustAllX509TrustManager")
                        @Override
                        public void checkServerTrusted (java.security.cert.X509Certificate[] chain, String authType) throws CertificateException {
                        }

                        @Override
                        public java.security.cert.X509Certificate[] getAcceptedIssuers () {
                            return new java.security.cert.X509Certificate[]{};
                        }
                    }
            };

            // Install the all-trusting trust manager
            final SSLContext sslContext = SSLContext.getInstance("TLS");
            sslContext.init(null, trustAllCerts, new java.security.SecureRandom());
            // Create an ssl socket factory with our all-trusting manager
            final SSLSocketFactory sslSocketFactory = sslContext.getSocketFactory();


            builder.sslSocketFactory(sslSocketFactory, (X509TrustManager) trustAllCerts[0]);
            builder.hostnameVerifier(new HostnameVerifier() {
                @SuppressLint("BadHostnameVerifier")
                @Override
                public boolean verify (String hostname, SSLSession session) {
                    return true;
                }
            });
        } catch (Exception e) {
            e.printStackTrace();
        }
        builder.connectTimeout(60, TimeUnit.SECONDS)
                .readTimeout(60, TimeUnit.SECONDS)
                .writeTimeout(60, TimeUnit.SECONDS)
                .retryOnConnectionFailure(true);
        return builder.build();
    }

    private Request createRequest (
            @NonNull final String relativeUrl,
            @NonNull final String content
    ) {
        final RequestBody body = RequestBody.create(JSON_TYPE, content);
        return new Request.Builder().
                url(mApiBaseUrl + relativeUrl).
                post(body).
                build();
    }

    private Request createRequest (
            @NonNull final String relativeUrl
    ) {
        return new Request.Builder().
                url(mApiBaseUrl + relativeUrl).
                build();
    }

    public ServerApiResponse sendRequestAndGetResponse (
            @NonNull final String relativeUrl,
            @NonNull final String content
    ) throws IOException {
        final Request request = createRequest(relativeUrl, content);
        final Response response = sendRequestAndGetRespone(request);
        return new ServerApiResponse(response.code(), response.body() != null ? response.body().string() : null);
    }

    public ServerApiResponse sendRequestAndGetResponse (
            @NonNull final String relativeUrl
    ) throws IOException {
        final Request request = createRequest(relativeUrl);
        final Response response = sendRequestAndGetRespone(request);
        return new ServerApiResponse(response.code(), response.body() != null ? response.body().string() : null);
    }

    public static Response sendRequestAndGetRespone (
            @NonNull final Request request
    ) throws IOException {
        return generateDefaultOkHttp().newCall(request).execute();
    }

    public <T extends ServerApiExecutor.ApiResult> T execute (
            @NonNull final ServerApiExecutor<T> serverApiExecutor
    ) throws Exception {
        return serverApiExecutor.execute(mApiBaseUrl, generateDefaultOkHttp());
    }

    @NonNull
    public String getApiBaseUrl () {
        return mApiBaseUrl;
    }
}
