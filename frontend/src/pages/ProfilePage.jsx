import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { userService, preferencesService } from '../services/apiService';

const FREQUENCY_LABELS = {
  daily: 'Daily',
  weekly: 'Weekly',
  realtime_critical: 'Real-time (critical alerts only)',
};

const ProfilePage = () => {
  const { logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Form states
  const [editingProfile, setEditingProfile] = useState(false);
  const [editingPreferences, setEditingPreferences] = useState(false);
  const [profileForm, setProfileForm] = useState({
    username: '',
    email: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [preferencesForm, setPreferencesForm] = useState({
    notification_type_email: true,
    notification_type_inapp: true,
    notification_frequency: 'daily',
  });

  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);
      setError('');

      try {
        // Fetch user profile
        const profileResponse = await userService.getMe();
        setProfile(profileResponse.data);
        setProfileForm({
          username: profileResponse.data.username || '',
          email: profileResponse.data.email || '',
          currentPassword: '',
          newPassword: '',
          confirmPassword: '',
        });

        // Fetch user preferences
        try {
          const preferencesResponse = await preferencesService.getPreferences();
          setPreferences(preferencesResponse.data);
          setPreferencesForm({
            notification_type_email: preferencesResponse.data.notification_type_email,
            notification_type_inapp: preferencesResponse.data.notification_type_inapp,
            notification_frequency: preferencesResponse.data.notification_frequency,
          });
        } catch (prefErr) {
          console.error('Error fetching preferences:', prefErr);
          // If preferences don't exist yet, use defaults
          setPreferences(null);
        }
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError('Failed to load your profile. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handlePreferencesChange = (e) => {
    const { name, value, type, checked } = e.target;
    setPreferencesForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    // Validate passwords if changing
    if (profileForm.newPassword) {
      if (!profileForm.currentPassword) {
        setError('Current password is required to set a new password');
        return;
      }
      if (profileForm.newPassword !== profileForm.confirmPassword) {
        setError('New passwords do not match');
        return;
      }
    }

    try {
      // Only send necessary fields
      const updateData = {
        username: profileForm.username,
        email: profileForm.email,
      };

      if (profileForm.newPassword) {
        updateData.current_password = profileForm.currentPassword;
        updateData.new_password = profileForm.newPassword;
      }

      const response = await userService.updateMe(updateData);
      setProfile(response.data.user);
      setSuccessMessage('Profile updated successfully');
      setEditingProfile(false);

      // Reset password fields
      setProfileForm((prev) => ({
        ...prev,
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      }));
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err.response?.data?.message || 'Failed to update profile. Please try again.');
    }
  };

  const handlePreferencesSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    try {
      const response = await preferencesService.updatePreferences(preferencesForm);
      setPreferences(response.data.preferences);
      setSuccessMessage('Preferences updated successfully');
      setEditingPreferences(false);
    } catch (err) {
      console.error('Error updating preferences:', err);
      setError(err.response?.data?.message || 'Failed to update preferences. Please try again.');
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      window.location.href = '/login';
    } catch (err) {
      console.error('Logout error:', err);
      setError('Failed to log out. Please try again.');
    }
  };

  return (
    <div className="profile-page">
      <h1>Your Profile</h1>

      {error && <div className="error-message">{error}</div>}
      {successMessage && <div className="success-message">{successMessage}</div>}

      {loading ? (
        <div className="loading">Loading your profile...</div>
      ) : (
        <div className="profile-content">
          <section className="profile-section">
            <div className="section-header">
              <h2>Account Information</h2>
              <button onClick={() => setEditingProfile(!editingProfile)} className="edit-button">
                {editingProfile ? 'Cancel' : 'Edit'}
              </button>
            </div>

            {editingProfile ? (
              <form onSubmit={handleProfileSubmit} className="profile-form">
                <div className="form-group">
                  <label htmlFor="username">Username</label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={profileForm.username}
                    onChange={handleProfileChange}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={profileForm.email}
                    onChange={handleProfileChange}
                    required
                  />
                </div>

                <h3>Change Password</h3>
                <p className="form-note">Leave blank to keep current password</p>

                <div className="form-group">
                  <label htmlFor="currentPassword">Current Password</label>
                  <input
                    type="password"
                    id="currentPassword"
                    name="currentPassword"
                    value={profileForm.currentPassword}
                    onChange={handleProfileChange}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="newPassword">New Password</label>
                  <input
                    type="password"
                    id="newPassword"
                    name="newPassword"
                    value={profileForm.newPassword}
                    onChange={handleProfileChange}
                    minLength="8"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="confirmPassword">Confirm New Password</label>
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    value={profileForm.confirmPassword}
                    onChange={handleProfileChange}
                  />
                </div>

                <div className="form-actions">
                  <button type="submit" className="save-button">
                    Save Changes
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingProfile(false)}
                    className="cancel-button"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="profile-info">
                <div className="info-item">
                  <span className="label">Username:</span>
                  <span className="value">{profile?.username}</span>
                </div>
                <div className="info-item">
                  <span className="label">Email:</span>
                  <span className="value">{profile?.email}</span>
                </div>
                <div className="info-item">
                  <span className="label">Account Created:</span>
                  <span className="value">
                    {profile?.created_at
                      ? new Date(profile.created_at).toLocaleDateString()
                      : 'N/A'}
                  </span>
                </div>
              </div>
            )}
          </section>

          <section className="profile-section">
            <div className="section-header">
              <h2>Preferences</h2>
              <button
                onClick={() => setEditingPreferences(!editingPreferences)}
                className="edit-button"
              >
                {editingPreferences ? 'Cancel' : 'Edit'}
              </button>
            </div>

            {editingPreferences ? (
              <form onSubmit={handlePreferencesSubmit} className="preferences-form">
                <div className="form-group checkbox">
                  <input
                    type="checkbox"
                    id="notification_type_email"
                    name="notification_type_email"
                    checked={preferencesForm.notification_type_email}
                    onChange={handlePreferencesChange}
                  />
                  <label htmlFor="notification_type_email">Email Notifications</label>
                </div>

                <div className="form-group checkbox">
                  <input
                    type="checkbox"
                    id="notification_type_inapp"
                    name="notification_type_inapp"
                    checked={preferencesForm.notification_type_inapp}
                    onChange={handlePreferencesChange}
                  />
                  <label htmlFor="notification_type_inapp">In-App Notifications</label>
                </div>

                <div className="form-group">
                  <label htmlFor="notification_frequency">Notification Frequency</label>
                  <select
                    id="notification_frequency"
                    name="notification_frequency"
                    value={preferencesForm.notification_frequency}
                    onChange={handlePreferencesChange}
                  >
                    {Object.entries(FREQUENCY_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-actions">
                  <button type="submit" className="save-button">
                    Save Preferences
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingPreferences(false)}
                    className="cancel-button"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="preferences-info">
                <div className="info-item">
                  <span className="label">Email Notifications:</span>
                  <span className="value">
                    {preferences?.notification_type_email ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="info-item">
                  <span className="label">In-App Notifications:</span>
                  <span className="value">
                    {preferences?.notification_type_inapp ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="info-item">
                  <span className="label">Notification Frequency:</span>
                  <span className="value">
                    {FREQUENCY_LABELS[preferences?.notification_frequency] || 'Daily'}
                  </span>
                </div>
              </div>
            )}
          </section>

          <section className="profile-section">
            <div className="section-header">
              <h2>Account Actions</h2>
            </div>
            <div className="account-actions">
              <button onClick={handleLogout} className="logout-button">
                Log Out
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
