package blagodarie.health.authentication;

import android.accounts.Account;
import android.accounts.AccountAuthenticatorResponse;
import android.accounts.AccountManager;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;
import androidx.navigation.NavController;
import androidx.navigation.NavDirections;
import androidx.navigation.Navigation;

import com.google.android.gms.auth.api.signin.GoogleSignIn;
import com.google.android.gms.auth.api.signin.GoogleSignInClient;
import com.google.android.gms.auth.api.signin.GoogleSignInOptions;

import blagodarie.health.authentication.R;
import blagodarie.health.authentication.StartFragmentDirections;

import java.util.Arrays;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/raw/master/LICENSE License
 */
public final class AuthenticationActivity
        extends AppCompatActivity
        implements AuthenticationNavigator {

    private static final String TAG = AuthenticationActivity.class.getSimpleName();

    private static final String EXTRA_ACCOUNT_TYPE = "blagodarie.health.authentication.ACCOUNT_TYPE";
    private static final String EXTRA_USER_ID = "blagodarie.health.authentication.USER_ID";
    private static final String EXTRA_IS_INCOGNITO_USER = "blagodarie.health.authentication.IS_INCOGNITO_USER";

    static final int ACTIVITY_REQUEST_CODE_GOGGLE_SIGN_IN = 1;

    private NavController mNavController;
    private AccountAuthenticatorResponse mAccountAuthenticatorResponse = null;
    private Bundle mResultBundle = null;

    @Override
    protected void onCreate (@Nullable Bundle savedInstanceState) {
        Log.d(TAG, "onCreate");

        super.onCreate(savedInstanceState);

        mAccountAuthenticatorResponse = getIntent().getParcelableExtra(AccountManager.KEY_ACCOUNT_AUTHENTICATOR_RESPONSE);

        if (mAccountAuthenticatorResponse != null) {
            mAccountAuthenticatorResponse.onRequestContinued();
        }

        setContentView(R.layout.authentication_activity);
        mNavController = Navigation.findNavController(this, R.id.nav_host_fragment);

        if (getIntent().hasExtra(EXTRA_USER_ID)) {
            toSignIn();
        } else {
            final Account[] accounts = AccountManager.get(this).getAccountsByType(getString(R.string.account_type));
            Log.d(TAG, "existing accounts=" + Arrays.toString(accounts));

            if (accounts.length > 0) {
                Toast.makeText(this, R.string.one_account_only, Toast.LENGTH_LONG).show();
                finish();
            } else {
                if (getIntent().getBooleanExtra(EXTRA_IS_INCOGNITO_USER, false)) {
                    toIncognitoSignUp();
                } else {
                    toGreeting();
                }
            }
        }

    }

    @Override
    public void onBackPressed () {
        Log.d(TAG, "onBackPressed");
        if (mNavController.getCurrentDestination() != null) {
            if (mNavController.getCurrentDestination().getId() == R.id.greetingFragment ||
                    mNavController.getCurrentDestination().getId() == R.id.signInFragment ||
                    mNavController.getCurrentDestination().getId() == R.id.incognitoSignUpFragment) {
                finish();
            } else {
                super.onBackPressed();
            }
        }
    }

    static void googleSignIn (
            @NonNull final Activity activity,
            @NonNull final Fragment fragment,
            @NonNull final String oauth2ClientId
    ) {
        Log.d(TAG, "googleSignIn");
        final GoogleSignInOptions gso = new GoogleSignInOptions.
                Builder(GoogleSignInOptions.DEFAULT_SIGN_IN).
                requestEmail().
                requestIdToken(oauth2ClientId).
                build();
        final GoogleSignInClient mGoogleSignInClient = GoogleSignIn.getClient(activity, gso);
        final Intent signInIntent = mGoogleSignInClient.getSignInIntent();
        fragment.startActivityForResult(signInIntent, ACTIVITY_REQUEST_CODE_GOGGLE_SIGN_IN);
    }

    public static Intent createSelfIntent (
            @NonNull final Context context,
            @NonNull final String accountType,
            final AccountAuthenticatorResponse response
    ) {
        Log.d(TAG, "createSelfIntent");
        final Intent intent = new Intent(context, AuthenticationActivity.class);
        intent.putExtra(EXTRA_ACCOUNT_TYPE, accountType);
        intent.putExtra(EXTRA_IS_INCOGNITO_USER, true);
        intent.putExtra(AccountManager.KEY_ACCOUNT_AUTHENTICATOR_RESPONSE, response);
        return intent;
    }

    public static Intent createSelfIntent (
            @NonNull final Context context,
            @NonNull final String accountType,
            @NonNull final Long userId,
            final AccountAuthenticatorResponse response
    ) {
        Log.d(TAG, "createSelfIntent");
        final Intent intent = createSelfIntent(context, accountType, response);
        intent.putExtra(EXTRA_USER_ID, userId);
        return intent;
    }

    @Override
    public void fromGreetingToSignUp () {
        Log.d(TAG, "fromGreetingToSignUp");
        mNavController.navigate(R.id.action_greetingFragment_to_signUpFragment);
    }

    @Override
    public void finish () {
        Log.d(TAG, "finish");
        if (mAccountAuthenticatorResponse != null) {
            if (mResultBundle != null) {
                mAccountAuthenticatorResponse.onResult(mResultBundle);
            } else {
                mAccountAuthenticatorResponse.onError(AccountManager.ERROR_CODE_CANCELED,
                        "canceled");
            }
            mAccountAuthenticatorResponse = null;
        }
        super.finish();
    }

    public final void setAccountAuthenticatorResult (Bundle result) {
        Log.d(TAG, "setAccountAuthenticatorResult result=" + result);
        mResultBundle = result;
    }

    void toGreeting () {
        Log.d(TAG, "toGreeting");
        mNavController.navigate(R.id.action_startFragment_to_greetingFragment);
    }

    void toIncognitoSignUp () {
        Log.d(TAG, "toIncognitoSignUp");
        mNavController.navigate(R.id.action_startFragment_to_incognitoSignUpFragment);
    }

    void toSignIn () {
        Log.d(TAG, "toSignIn");
        final long badUserId = Long.MIN_VALUE;
        final long userId = getIntent().getLongExtra(EXTRA_USER_ID, badUserId);
        if (userId != badUserId) {
            final NavDirections action = StartFragmentDirections.actionStartFragmentToSignInFragment(userId);
            mNavController.navigate(action);
        } else {
            Toast.makeText(this, R.string.error_bad_user_id, Toast.LENGTH_SHORT).show();
            finish();
        }
    }
}
