package org.blagodarie.authentication;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

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
import org.blagodarie.server.ServerDataSource;

import io.reactivex.Observable;
import io.reactivex.android.schedulers.AndroidSchedulers;
import io.reactivex.disposables.CompositeDisposable;
import io.reactivex.schedulers.Schedulers;

import static android.app.Activity.RESULT_OK;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class EnterFragment
        extends Fragment {

    private static final int ACTIVITY_REQUEST_CODE_GOGGLE_SIGN_IN = 1;

    private CompositeDisposable mDisposables = new CompositeDisposable();

    @Override
    public View onCreateView (@NonNull LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        final EnterFragmentBinding mEnterFragmentBinding = EnterFragmentBinding.inflate(inflater, container, false);
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
                        account.getId() != null) {
                    startGetUserIdFromServer(account.getId());
                }
            } catch (ApiException e) {
                String err = e.getMessage();
            }
        }
    }

    private void signIn () {
        final GoogleSignInOptions gso = new GoogleSignInOptions.
                Builder(GoogleSignInOptions.DEFAULT_SIGN_IN).
                requestEmail().
                build();
        final GoogleSignInClient mGoogleSignInClient = GoogleSignIn.getClient(requireActivity(), gso);
        final Intent signInIntent = mGoogleSignInClient.getSignInIntent();
        startActivityForResult(signInIntent, ACTIVITY_REQUEST_CODE_GOGGLE_SIGN_IN);
    }

    private void startGetUserIdFromServer (@NonNull final String googleAccountId) {
        final ServerDataSource serverDataSource = new ServerDataSource(requireContext());
        mDisposables.add(
                Observable.
                        fromCallable(() -> serverDataSource.getUserId(googleAccountId)).
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
                            ((AuthenticationActivity) requireActivity()).setAccountAuthenticatorResult(data);
                            requireActivity().setResult(RESULT_OK, res);
                            requireActivity().finish();
                        })
        );
    }


}
