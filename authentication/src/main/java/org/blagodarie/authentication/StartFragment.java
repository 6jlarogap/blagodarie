package org.blagodarie.authentication;

import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/raw/master/LICENSE License
 */
public final class StartFragment
        extends Fragment {

    private static final String TAG = StartFragment.class.getSimpleName();

    @Override
    public View onCreateView (
            @NonNull final LayoutInflater inflater,
            final ViewGroup container,
            final Bundle savedInstanceState
    ) {
        Log.d(TAG, "onCreateView");
        return inflater.inflate(R.layout.start_fragment, container, false);
    }

}
