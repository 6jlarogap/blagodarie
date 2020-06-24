package blagodarie.health.ui.symptoms;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

final class VersionName {

    private static final String VERSION_NAME_PATTERN = "^\\d+\\.\\d+\\.\\d+$";
    private final int MajorSegment;
    private final int MiddleSegment;
    private final int MinorSegment;

    VersionName (final String versionName) {
        final Pattern pattern = Pattern.compile(VERSION_NAME_PATTERN);
        final Matcher matcher = pattern.matcher(versionName);
        if (matcher.matches()) {
            final String[] versionNameSegments = versionName.split("\\.");
            MajorSegment = Integer.parseInt(versionNameSegments[0]);
            MiddleSegment = Integer.parseInt(versionNameSegments[1]);
            MinorSegment = Integer.parseInt(versionNameSegments[2]);
        } else {
            throw new IllegalArgumentException("Incorrect version name string: " + versionName);
        }
    }

    public int getMajorSegment () {
        return MajorSegment;
    }

    public int getMiddleSegment () {
        return MiddleSegment;
    }

    public int getMinorSegment () {
        return MinorSegment;
    }

    @Override
    public String toString () {
        return MajorSegment + "." + MiddleSegment + "." + MinorSegment;
    }
}