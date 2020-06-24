package blagodarie.health.authentication;

import android.accounts.AccountManager;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
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

import blagodarie.health.authentication.R;
import blagodarie.health.authentication.SignInFragmentArgs;

import blagodarie.health.server.ServerApiExecutor;
import blagodarie.health.server.ServerApiResponse;
import blagodarie.health.server.ServerConnector;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.Locale;

import io.reactivex.Observable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.schedulers.Schedulers;

import static android.app.Activity.RESULT_OK;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/raw/master/LICENSE License
 */
public final class SignInFragment
        extends Fragment {

    private static final String TAG = SignInFragment.class.getSimpleName();

    private static final class SignInExecutor {

        private static final String TAG = SignInExecutor.class.getSimpleName();

        private static final class ApiResult
                extends ServerApiExecutor.ApiResult {

            @NonNull
            private final String mToken;

            ApiResult (
                    @NonNull final String token
            ) {
                mToken = token;
            }

            @NonNull
            String getToken () {
                return mToken;
            }
        }

        private static final String JSON_PATTERN = "{\"oauth\":{\"provider\":\"google\",\"token\":\"%s\"},\"user_id\":%d}";

        @NonNull
        private final String mGoogleTokenId;

        @NonNull
        private final Long mUserId;

        private SignInExecutor (
                @NonNull final String googleTokenId,
                @NonNull final Long userId
        ) {
            mGoogleTokenId = googleTokenId;
            mUserId = userId;
        }

        public SignInExecutor.ApiResult execute (
                @NonNull final ServerConnector serverConnector
        ) throws JSONException, IOException {
            Log.d(TAG, "execute");
            String authToken = null;

            final String content = String.format(Locale.ENGLISH, JSON_PATTERN, mGoogleTokenId, mUserId);
            Log.d(TAG, "content=" + content);

            final ServerApiResponse serverApiResponse = serverConnector.sendRequestAndGetResponse("auth/signin", content);
            Log.d(TAG, "serverApiResponse=" + serverApiResponse);

            if (serverApiResponse.getCode() == 200) {
                if (serverApiResponse.getBody() != null) {
                    final String responseBody = serverApiResponse.getBody();
                    final JSONObject userJSON = new JSONObject(responseBody);
                    authToken = userJSON.getString("token");
                }
            }
            return new SignInExecutor.ApiResult(authToken);

        }
    }

    private Long mUserId;

    private CompositeDisposable mDisposables = new CompositeDisposable();

    @Override
    public View onCreateView (
            @NonNull final LayoutInflater inflater,
            final ViewGroup container,
            final Bundle savedInstanceState
    ) {
        Log.d(TAG, "onCreateView");
        final View view = inflater.inflate(R.layout.sign_in_fragment, container, false);
        initViews(view);
        return view;
    }

    @Override
    public void onViewCreated (
            @NonNull final View view,
            @Nullable final Bundle savedInstanceState
    ) {
        Log.d(TAG, "onViewCreated");
        super.onViewCreated(view, savedInstanceState);
        if (getArguments() != null) {
            mUserId = SignInFragmentArgs.fromBundle(getArguments()).getUserId();
        } else {
            throw new IllegalArgumentException("No required parameters");
        }
    }

    @Override
    public void onActivityCreated (@Nullable Bundle savedInstanceState) {
        Log.d(TAG, "onActivityCreated");
        super.onActivityCreated(savedInstanceState);
        AuthenticationActivity.googleSignIn(
                requireActivity(),
                this,
                getString(R.string.oauth2_client_id)
        );
    }

    @Override
    public void onDestroy () {
        Log.d(TAG, "onDestroy");
        super.onDestroy();
        mDisposables.dispose();
    }


    private void initViews (View view) {
        Log.d(TAG, "initViews");
        view.findViewById(R.id.btnSignIn).setOnClickListener(
                v -> AuthenticationActivity.googleSignIn(
                        requireActivity(),
                        this,
                        getString(R.string.oauth2_client_id)
                )
        );
    }

    @Override
    public void onActivityResult (
            final int requestCode,
            final int resultCode,
            @Nullable final Intent data
    ) {
        Log.d(TAG, "onActivityResult");
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == AuthenticationActivity.ACTIVITY_REQUEST_CODE_GOGGLE_SIGN_IN) {
            final Task<GoogleSignInAccount> task = GoogleSignIn.getSignedInAccountFromIntent(data);
            try {
                final GoogleSignInAccount account = task.getResult(ApiException.class);
                if (account != null &&
                        account.getIdToken() != null) {
                    startSignIn(account.getIdToken());
                }
            } catch (ApiException e) {
                Toast.makeText(requireActivity(), e.getMessage(), Toast.LENGTH_LONG).show();
            }
        }
    }

    private void startSignIn (
            @NonNull final String googleTokenId
    ) {
        Log.d(TAG, "startSignIn");
        final ServerConnector serverConnector = new ServerConnector(requireContext());
        final SignInExecutor signInExecutor = new SignInExecutor(googleTokenId, mUserId);
        mDisposables.add(
                Observable.
                        fromCallable(
                                () -> signInExecutor.execute(serverConnector)
                        ).
                        subscribeOn(Schedulers.io()).
                        observeOn(AndroidSchedulers.mainThread()).
                        subscribe(
                                apiResult -> finishSignIn(apiResult.getToken()),
                                throwable -> Toast.makeText(requireActivity(), throwable.getMessage(), Toast.LENGTH_LONG).show()
                        )
        );
    }

    private void finishSignIn (
            @NonNull final String authToken
    ) {
        Log.d(TAG, "finishSignIn");
        final Bundle bundle = new Bundle();
        bundle.putString(AccountManager.KEY_ACCOUNT_NAME, mUserId.toString());
        bundle.putString(AccountManager.KEY_ACCOUNT_TYPE, getString(R.string.account_type));
        bundle.putString(AccountManager.KEY_AUTHTOKEN, authToken);
        final Intent res = new Intent();
        res.putExtras(bundle);

        ((AuthenticationActivity) requireActivity()).setAccountAuthenticatorResult(bundle);
        requireActivity().setResult(RESULT_OK, res);
        requireActivity().finish();
    }

}
