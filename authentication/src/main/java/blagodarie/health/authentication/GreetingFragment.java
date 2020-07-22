package blagodarie.health.authentication;

import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import blagodarie.health.authentication.databinding.GreetingFragmentBinding;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/raw/master/LICENSE License
 */
public final class GreetingFragment
        extends Fragment {

    private static final String TAG = GreetingFragment.class.getSimpleName();

    private GreetingFragmentBinding mGreetingFragmentBinding;

    @Override
    public View onCreateView (
            @NonNull final LayoutInflater inflater,
            final ViewGroup container,
            final Bundle savedInstanceState
    ) {
        Log.d(TAG, "onCreateView");
        mGreetingFragmentBinding = GreetingFragmentBinding.inflate(inflater, container, false);
        return mGreetingFragmentBinding.getRoot();
    }

    @Override
    public void onActivityCreated (@Nullable final Bundle savedInstanceState) {
        Log.d(TAG, "onActivityCreated");
        super.onActivityCreated(savedInstanceState);
        mGreetingFragmentBinding.setAuthenticationNavigator((AuthenticationNavigator) getActivity());
    }
}
