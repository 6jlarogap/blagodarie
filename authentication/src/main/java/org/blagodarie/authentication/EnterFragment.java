package org.blagodarie.authentication;

import android.accounts.Account;
import android.accounts.AccountAuthenticatorActivity;
import android.accounts.AccountManager;
import android.annotation.SuppressLint;
import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.google.android.gms.auth.api.signin.GoogleSignIn;
import com.google.android.gms.auth.api.signin.GoogleSignInAccount;
import com.google.android.gms.auth.api.signin.GoogleSignInClient;
import com.google.android.gms.auth.api.signin.GoogleSignInOptions;
import com.google.android.gms.common.api.ApiException;
import com.google.android.gms.tasks.Task;

import org.blagodarie.authentication.databinding.EnterFragmentBinding;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.security.cert.CertificateException;
import java.util.Locale;
import java.util.concurrent.TimeUnit;

import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSession;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

import io.reactivex.Observable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.schedulers.Schedulers;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

import static android.app.Activity.RESULT_OK;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class EnterFragment
        extends Fragment {

    private static final int ACTIVITY_REQUEST_CODE_GOGGLE_SIGN_IN = 1;

    private EnterFragmentBinding mEnterFragmentBinding;
    private Button mBtnSingIn;

    @Override
    public View onCreateView (@NonNull LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        this.mEnterFragmentBinding = EnterFragmentBinding.inflate(inflater, container, false);
        final View view = mEnterFragmentBinding.getRoot();
        initViews(view);
        return view;
    }

    @Override
    public void onActivityCreated (@Nullable Bundle savedInstanceState) {
        super.onActivityCreated(savedInstanceState);
    }

    private void initViews (View view) {
        view.findViewById(R.id.btnSignIn).setOnClickListener(v -> signIn());
    }

    @Override
    public void onStart () {
        super.onStart();
        signIn();
    }

    @Override
    public void onResume () {
        super.onResume();
    }

    @Override
    public void onActivityResult (
            final int requestCode,
            final int resultCode,
            @Nullable final Intent data
    ) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == ACTIVITY_REQUEST_CODE_GOGGLE_SIGN_IN) {
            final Task<GoogleSignInAccount> task = GoogleSignIn.getSignedInAccountFromIntent(data);
            try {
                final GoogleSignInAccount account = task.getResult(ApiException.class);
                if (account != null &&
                        account.getId() != null) {
                    startGetUserIdFromServer(account.getId());
                }
            } catch (ApiException e) {
                String err = e.getMessage();
            }
        }
    }

    private void signIn () {
        final GoogleSignInOptions gso = new GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
                .requestEmail()
                .build();
        final GoogleSignInClient mGoogleSignInClient = GoogleSignIn.getClient(requireActivity(), gso);
        final Intent signInIntent = mGoogleSignInClient.getSignInIntent();
        startActivityForResult(signInIntent, ACTIVITY_REQUEST_CODE_GOGGLE_SIGN_IN);
    }

    private void startGetUserIdFromServer (@NonNull final String googleAccountId) {
        Observable.
                fromCallable(() -> getUserIdFromServer(googleAccountId)).
                subscribeOn(Schedulers.io()).
                observeOn(AndroidSchedulers.mainThread()).
                subscribe(userId -> {
                    Account account = new Account(userId.toString(), getString(R.string.account_type));
                    Bundle data = new Bundle();
                    data.putString(AccountManager.KEY_ACCOUNT_NAME, userId.toString());
                    data.putString(AccountManager.KEY_ACCOUNT_TYPE, getString(R.string.account_type));
                    data.putString(AccountManager.KEY_AUTHTOKEN, "token");
                    final Intent res = new Intent();
                    res.putExtras(data);

                    AccountManager.get(getContext()).addAccountExplicitly(account, "", null);
                    ((AuthenticationActivity)requireActivity()).setAccountAuthenticatorResult(data);
                    requireActivity().setResult(RESULT_OK, res);
                    requireActivity().finish();
                });
    }

    private Long getUserIdFromServer (@NonNull final String googleAccountId)
            throws IOException, JSONException {
        Long userId = null;
        final Request request = new Request.Builder()
                .url("https://api.dev.благодарие.рф/api/getorcreateuser" + String.format(Locale.ENGLISH, "?googleaccountid=%s", googleAccountId))
                .build();
        final Response response = sendRequestAndGetResponse(request);
        if (response.body() != null) {
            final String responseBody = response.body().string();
            if (response.code() == 200) {
                final JSONObject rootJSON = new JSONObject(responseBody);
                final JSONObject userJSON = rootJSON.getJSONObject("user");
                userId = userJSON.getLong("server_id");
            }
        }
        return userId;
    }

    private static Response sendRequestAndGetResponse (@NonNull final Request request)
            throws IOException {
        return generateDefaultOkHttp().newCall(request).execute();
    }

    @NonNull
    private static OkHttpClient generateDefaultOkHttp () {
        final OkHttpClient.Builder builder = new OkHttpClient.Builder();
        try {
            // Create a trust manager that does not validate certificate chains
            final TrustManager[] trustAllCerts = new TrustManager[]{
                    new X509TrustManager() {
                        @SuppressLint ("TrustAllX509TrustManager")
                        @Override
                        public void checkClientTrusted (java.security.cert.X509Certificate[] chain, String authType) throws CertificateException {
                        }

                        @SuppressLint ("TrustAllX509TrustManager")
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
            final SSLContext sslContext = SSLContext.getInstance("SSL");
            sslContext.init(null, trustAllCerts, new java.security.SecureRandom());
            // Create an ssl socket factory with our all-trusting manager
            final SSLSocketFactory sslSocketFactory = sslContext.getSocketFactory();


            builder.sslSocketFactory(sslSocketFactory, (X509TrustManager) trustAllCerts[0]);
            builder.hostnameVerifier(new HostnameVerifier() {
                @SuppressLint ("BadHostnameVerifier")
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

}
