import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AuthContext, api } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, Globe, LogOut, User } from 'lucide-react';
import { toast } from 'sonner';
import { SUPPORTED_LANGUAGES } from '../i18n';
import { SubscriptionSection } from '../components/SubscriptionSection';

export const Settings = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { user, logout, setUser } = useContext(AuthContext);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const changeLanguage = async (lang) => {
    // Update UI immediately
    i18n.changeLanguage(lang);
    
    // Persist to backend
    try {
      await api.patch('/auth/me', { language: lang });
      
      // Update cached user
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      const updatedUser = { ...currentUser, language: lang };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      // Update context if setUser is available
      if (setUser) {
        setUser(updatedUser);
      }
      
      toast.success(t('settings.languageChanged'));
    } catch (error) {
      console.error('Failed to save language:', error);
    }
  };

  const handlePlanChange = () => {
    // Refresh user data after plan change
    const refreshUser = async () => {
      try {
        const response = await api.get('/auth/me');
        setUser(response.data);
        localStorage.setItem('user', JSON.stringify(response.data));
      } catch (error) {
        console.error('Failed to refresh user:', error);
      }
    };
    refreshUser();
  };

  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 py-4 sm:py-6">
        <div className="flex items-center gap-3 sm:gap-4 mb-6 sm:mb-8">
          <Button
            data-testid="back-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/albums')}
            className="flex-shrink-0"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-xl sm:text-3xl font-black tracking-tight text-primary truncate">{t('settings.title')}</h1>
        </div>

        <div className="space-y-4 sm:space-y-6">
          {/* Subscription Section - Prominent placement */}
          <SubscriptionSection onPlanChange={handlePlanChange} />

          <Card data-testid="profile-card">
            <CardHeader className="pb-2 sm:pb-4 px-4 sm:px-6 pt-4 sm:pt-6">
              <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
                <User className="h-4 w-4 sm:h-5 sm:w-5" />
                {t('settings.profile')}
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 sm:px-6 pb-4 sm:pb-6">
              <Button
                data-testid="profile-btn"
                variant="outline"
                className="w-full text-sm sm:text-base"
                onClick={() => navigate('/profile')}
              >
                {t('profile.title')}
              </Button>
            </CardContent>
          </Card>

          <Card data-testid="user-info-card">
            <CardHeader className="pb-2 sm:pb-4 px-4 sm:px-6 pt-4 sm:pt-6">
              <CardTitle className="text-base sm:text-lg truncate">{user?.display_name || user?.email}</CardTitle>
            </CardHeader>
            <CardContent className="px-4 sm:px-6 pb-4 sm:pb-6">
              <p className="text-sm sm:text-base text-muted-foreground truncate">{user?.email}</p>
            </CardContent>
          </Card>

          <Card data-testid="language-card">
            <CardHeader className="pb-2 sm:pb-4 px-4 sm:px-6 pt-4 sm:pt-6">
              <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
                <Globe className="h-4 w-4 sm:h-5 sm:w-5" />
                {t('settings.language')}
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 sm:px-6 pb-4 sm:pb-6">
              <Select value={i18n.language} onValueChange={changeLanguage}>
                <SelectTrigger data-testid="language-select" className="w-full">
                  <SelectValue placeholder={t('settings.language')} />
                </SelectTrigger>
                <SelectContent>
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <SelectItem 
                      key={lang.code} 
                      value={lang.code}
                      data-testid={`lang-${lang.code}`}
                    >
                      <span className="flex items-center gap-2">
                        <span>{lang.flag}</span>
                        <span>{lang.name}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          <Card data-testid="logout-card">
            <CardContent className="pt-4 sm:pt-6 px-4 sm:px-6 pb-4 sm:pb-6">
              <Button
                data-testid="logout-btn"
                variant="destructive"
                className="w-full text-sm sm:text-base"
                onClick={handleLogout}
              >
                <LogOut className="h-5 w-5 mr-2" />
                {t('settings.logout')}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Settings;
