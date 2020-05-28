package org.blagodarie.authentication;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.databinding.DataBindingUtil;
import androidx.fragment.app.Fragment;

import org.blagodarie.authentication.databinding.IncognitoSignUpFragmentBinding;

import java.util.UUID;

import static android.app.Activity.RESULT_OK;

public final class IncognitoSignUpFragment
        extends Fragment {

    public interface IncognitoSignUpUserAction {

        void createNewIncognitoId ();

        void enterExistingIncognitoId ();

    }

    private static final String TAG = IncognitoSignUpFragment.class.getSimpleName();

    @Override
    public View onCreateView (
            @NonNull final LayoutInflater inflater,
            final ViewGroup container,
            final Bundle savedInstanceState
    ) {
        Log.d(TAG, "onCreateView");
        final IncognitoSignUpFragmentBinding binding = DataBindingUtil.inflate(inflater, R.layout.incognito_sign_up_fragment, null, false);
        binding.setIncognitoSignUpUserActionListener(new IncognitoSignUpUserAction() {
            @Override
            public void createNewIncognitoId () {
                createIncognitoAccount(UUID.randomUUID());
            }

            @Override
            public void enterExistingIncognitoId () {
                showIncognitoIdDialog();
            }
        });
        return binding.getRoot();
    }

    private void showIncognitoIdDialog () {
        Log.e(TAG, "showIncognitoIdDialog");
        final View view = getLayoutInflater().inflate(R.layout.enter_incognito_id_dialog, null, false);

        final ClipboardManager clipboard = (ClipboardManager) requireContext().getSystemService(Context.CLIPBOARD_SERVICE);
        final ClipData clipData = clipboard.getPrimaryClip();
        if (clipData != null) {
            final ClipData.Item item = clipboard.getPrimaryClip().getItemAt(0);
            final String incognitoIdString = item.getText().toString();
            try {
                final UUID incognitoId = UUID.fromString(incognitoIdString);
                ((EditText) view.findViewById(R.id.etIncognitoId)).setText(incognitoId.toString());
            } catch (IllegalArgumentException e) {
                Log.e(TAG, "error=" + e);
            }
        }

        final AlertDialog alertDialog = new AlertDialog.
                Builder(requireContext()).
                setView(view).
                setNeutralButton(R.string.btn_back, null).
                setNegativeButton(R.string.btn_paste, null).
                setPositiveButton(R.string.btn_continue, (dialog, which) -> {
                    final String incognitoIdString = ((EditText) view.findViewById(R.id.etIncognitoId)).getText().toString();
                    try {
                        final UUID incognitoId = UUID.fromString(incognitoIdString);
                        createIncognitoAccount(incognitoId);
                    } catch (IllegalArgumentException e) {
                        Toast.makeText(requireContext(), getString(R.string.err_msg_incorrect_incognito_id), Toast.LENGTH_SHORT).show();
                    }
                }).
                create();

        alertDialog.show();

        alertDialog.getButton(DialogInterface.BUTTON_NEGATIVE).setOnClickListener(v -> {
            final ClipData.Item item = clipboard.getPrimaryClip().getItemAt(0);
            final String bufferString = item.getText().toString();
            ((EditText) view.findViewById(R.id.etIncognitoId)).setText(bufferString);
        });
    }

    private void createIncognitoAccount (
            @NonNull final UUID incognitoPrivateKey
    ) {
        Log.d(TAG, "createAccount");
        final String accountName = getString(R.string.incognito_account_name);
        final AccountManager accountManager = AccountManager.get(getContext());
        final Account account = new Account(accountName, getString(R.string.account_type));
        final Bundle userData = new Bundle();
        userData.putString(AccountGeneral.USER_DATA_INCOGNITO_PRIVATE_KEY, incognitoPrivateKey.toString());
        accountManager.addAccountExplicitly(account, "", userData);

        final Bundle bundle = new Bundle();
        bundle.putString(AccountManager.KEY_ACCOUNT_NAME, accountName);
        bundle.putString(AccountManager.KEY_ACCOUNT_TYPE, getString(R.string.account_type));
        //bundle.putString(AccountManager.KEY_AUTHTOKEN, authToken);
        final Intent res = new Intent();
        res.putExtras(bundle);

        ((AuthenticationActivity) requireActivity()).setAccountAuthenticatorResult(bundle);
        requireActivity().setResult(RESULT_OK, res);
        requireActivity().finish();
    }
}
