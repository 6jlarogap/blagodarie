package org.blagodarie.authentication;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.google.android.gms.auth.api.signin.GoogleSignIn;
import com.google.android.gms.auth.api.signin.GoogleSignInAccount;
import com.google.android.gms.common.api.ApiException;
import com.google.android.gms.tasks.Task;

import org.blagodarie.server.ServerApiExecutor;
import org.blagodarie.server.ServerConnector;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.Locale;
import java.util.UUID;

import io.reactivex.Observable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.schedulers.Schedulers;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

import static android.app.Activity.RESULT_OK;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class SignUpFragment
        extends Fragment {

    private static final class SignUpExecutor
            implements ServerApiExecutor<SignUpExecutor.ApiResult> {

        private static final class ApiResult
                extends ServerApiExecutor.ApiResult {

            @NonNull
            private final String mUserId;

            @NonNull
            private final String mToken;

            ApiResult (
                    @NonNull final String userId,
                    @NonNull final String token
            ) {
                mUserId = userId;
                mToken = token;
            }

            @NonNull
            String getUserId () {
                return mUserId;
            }

            @NonNull
            String getToken () {
                return mToken;
            }
        }

        @NonNull
        private final String mGoogleAccountId;

        @NonNull
        private final String mGoogleTokenId;

        private SignUpExecutor (
                @NonNull final String googleAccountId,
                @NonNull final String googleTokenId
        ) {
            this.mGoogleAccountId = googleAccountId;
            this.mGoogleTokenId = googleTokenId;
        }

        @Override
        public SignUpExecutor.ApiResult execute (
                @NonNull String apiBaseUrl,
                @NonNull OkHttpClient okHttpClient
        ) throws JSONException, IOException {
            Long userId = null;
            final Request request = new Request.Builder()
                    .url(apiBaseUrl + "getorcreateuser" + String.format(Locale.ENGLISH, "?googleaccountid=%s", mGoogleAccountId))
                    .build();
            final Response response = okHttpClient.newCall(request).execute();
            if (response.body() != null) {
                final String responseBody = response.body().string();
                if (response.code() == 200) {
                    final JSONObject userJSON = new JSONObject(responseBody).getJSONObject("user");
                    userId = userJSON.getLong("server_id");
                }
            }
            return new ApiResult(userId.toString(), "token-from-sign-up:" + UUID.randomUUID().toString());
        }
    }

    private static final int ACTIVITY_REQUEST_CODE_GOGGLE_SIGN_IN = 1;

    private CompositeDisposable mDisposables = new CompositeDisposable();

    @Override
    public View onCreateView (
            @NonNull final LayoutInflater inflater,
            final ViewGroup container,
            final Bundle savedInstanceState) {
        final View view = inflater.inflate(R.layout.sign_up_fragment, container, false);
        initViews(view);
        return view;
    }


    @Override
    public void onActivityCreated (@Nullable Bundle savedInstanceState) {
        super.onActivityCreated(savedInstanceState);
        AuthenticationActivity.googleSignIn(requireActivity(), this, getString(R.string.oauth2_client_id));
    }

    private void initViews (View view) {
        view.findViewById(R.id.btnSignIn).setOnClickListener(v -> AuthenticationActivity.googleSignIn(requireActivity(), this, getString(R.string.oauth2_client_id)));
    }

    @Override
    public void onDestroy () {
        super.onDestroy();
        mDisposables.dispose();
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
                        account.getId() != null &&
                        account.getIdToken() != null) {
                    startSignUp(account.getId(), account.getIdToken());
                }
            } catch (ApiException e) {
                Toast.makeText(requireActivity(), e.getMessage(), Toast.LENGTH_LONG).show();
            }
        }
    }

    private void startSignUp (
            @NonNull final String googleAccountId,
            @NonNull final String googleTokenId
    ) {
        final ServerConnector serverConnector = new ServerConnector(requireContext());
        final SignUpExecutor signUpExecutor = new SignUpExecutor(googleAccountId, googleTokenId);
        mDisposables.add(
                Observable.
                        fromCallable(() -> serverConnector.execute(signUpExecutor)).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(
                                apiResult -> createAccount(apiResult.getUserId(), apiResult.getToken()),
                                throwable -> Toast.makeText(requireActivity(), throwable.getMessage(), Toast.LENGTH_LONG).show()
                        )
        );
    }

    private void createAccount (
            @NonNull final String accountName,
            @NonNull final String authToken
    ) {
        final AccountManager accountManager = AccountManager.get(getContext());
        final Account account = new Account(accountName, getString(R.string.account_type));
        accountManager.addAccountExplicitly(account, "", null);
        accountManager.setAuthToken(account, getString(R.string.token_type), authToken);

        final Bundle bundle = new Bundle();
        bundle.putString(AccountManager.KEY_ACCOUNT_NAME, accountName);
        bundle.putString(AccountManager.KEY_ACCOUNT_TYPE, getString(R.string.account_type));
        bundle.putString(AccountManager.KEY_AUTHTOKEN, authToken);
        final Intent res = new Intent();
        res.putExtras(bundle);

        ((AuthenticationActivity) requireActivity()).setAccountAuthenticatorResult(bundle);
        requireActivity().setResult(RESULT_OK, res);
        requireActivity().finish();
    }

}