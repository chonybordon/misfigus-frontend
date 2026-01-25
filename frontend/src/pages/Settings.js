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

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button
            data-testid="back-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/albums')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-3xl font-black tracking-tight text-primary">{t('settings.title')}</h1>
        </div>

        <div className="space-y-6">
          <Card data-testid="profile-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                {t('settings.profile')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Button
                data-testid="profile-btn"
                variant="outline"
                className="w-full"
                onClick={() => navigate('/profile')}
              >
                {t('profile.title')}
              </Button>
            </CardContent>
          </Card>

          <Card data-testid="user-info-card">
            <CardHeader>
              <CardTitle>{user?.display_name || user?.email}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">{user?.email}</p>
            </CardContent>
          </Card>

          <Card data-testid="language-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                {t('settings.language')}
              </CardTitle>
            </CardHeader>
            <CardContent>
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
            <CardContent className="pt-6">
              <Button
                data-testid="logout-btn"
                variant="destructive"
                className="w-full"
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
