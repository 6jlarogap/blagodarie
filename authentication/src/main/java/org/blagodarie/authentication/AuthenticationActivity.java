package org.blagodarie.authentication;

import android.accounts.Account;
import android.accounts.AccountAuthenticatorResponse;
import android.accounts.AccountManager;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
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

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class AuthenticationActivity
        extends AppCompatActivity
        implements AuthenticationNavigator {

    private static final String EXTRA_ACCOUNT_TYPE = "org.blagodarie.authentication.ACCOUNT_TYPE";
    static final String EXTRA_USER_ID = "org.blagodarie.authentication.USER_ID";

    static final int ACTIVITY_REQUEST_CODE_GOGGLE_SIGN_IN = 1;

    private NavController mNavController;
    private AccountAuthenticatorResponse mAccountAuthenticatorResponse = null;
    private Bundle mResultBundle = null;

    @Override
    protected void onCreate (@Nullable Bundle savedInstanceState) {
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

            if (accounts.length > 0) {
                Toast.makeText(this, R.string.one_account_only, Toast.LENGTH_LONG).show();
                finish();
            } else {
                toGreeting();
            }
        }

    }

    static void googleSignIn (
            @NonNull final Activity activity,
            @NonNull final Fragment fragment,
            @NonNull final String oauth2ClientId
    ) {
        final GoogleSignInOptions gso = new GoogleSignInOptions.
                Builder(GoogleSignInOptions.DEFAULT_SIGN_IN).
                requestEmail().
                requestIdToken(oauth2ClientId).
                build();
        final GoogleSignInClient mGoogleSignInClient = GoogleSignIn.getClient(activity, gso);
        final Intent signInIntent = mGoogleSignInClient.getSignInIntent();
        fragment.startActivityForResult(signInIntent, ACTIVITY_REQUEST_CODE_GOGGLE_SIGN_IN);
    }

    public static Intent createIntent (
            @NonNull final Context context,
            @NonNull final String accountType,
            final AccountAuthenticatorResponse response
    ) {
        final Intent intent = new Intent(context, AuthenticationActivity.class);
        intent.putExtra(AuthenticationActivity.EXTRA_ACCOUNT_TYPE, accountType);
        intent.putExtra(AccountManager.KEY_ACCOUNT_AUTHENTICATOR_RESPONSE, response);
        return intent;
    }

    public static Intent createIntent (
            @NonNull final Context context,
            @NonNull final String accountType,
            @NonNull final Long userId,
            final AccountAuthenticatorResponse response
    ) {
        final Intent intent = createIntent(context, accountType, response);
        intent.putExtra(EXTRA_USER_ID, userId);
        return intent;
    }

    @Override
    public void fromGreetingToSignUp () {
        mNavController.navigate(R.id.action_greetingFragment_to_signUpFragment);
    }

    @Override
    public void finish () {
        if (mAccountAuthenticatorResponse != null) {
            // send the result bundle back if set, otherwise send an error.
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
        mResultBundle = result;
    }

    void toGreeting () {
        mNavController.navigate(R.id.action_startFragment_to_greetingFragment);
    }

    void toSignIn () {
        final NavDirections action = StartFragmentDirections.actionStartFragmentToSignInFragment(getIntent().getLongExtra(EXTRA_USER_ID, -1));
        mNavController.navigate(action);
    }
}
