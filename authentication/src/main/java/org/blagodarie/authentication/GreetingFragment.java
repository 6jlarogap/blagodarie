package org.blagodarie.authentication;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import org.blagodarie.authentication.databinding.GreetingFragmentBinding;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
public final class GreetingFragment
        extends Fragment {

    private GreetingFragmentBinding mGreetingFragmentBinding;

    @Override
    public View onCreateView (
            @NonNull final LayoutInflater inflater,
            final ViewGroup container,
            final Bundle savedInstanceState
    ) {
        this.mGreetingFragmentBinding = GreetingFragmentBinding.inflate(inflater, container, false);
        return this.mGreetingFragmentBinding.getRoot();
    }

    @Override
    public void onActivityCreated (@Nullable final Bundle savedInstanceState) {
        super.onActivityCreated(savedInstanceState);
        this.mGreetingFragmentBinding.setAuthenticationNavigator((AuthenticationNavigator) getActivity());
    }
}
