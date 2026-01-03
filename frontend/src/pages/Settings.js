import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AuthContext } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Globe, LogOut } from 'lucide-react';

export const Settings = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { user, logout } = useContext(AuthContext);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const changeLanguage = (lang) => {
    i18n.changeLanguage(lang);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button
            data-testid="back-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/groups')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-3xl font-black tracking-tight text-primary">{t('settings.title')}</h1>
        </div>

        <div className="space-y-6">
          <Card data-testid="user-info-card">
            <CardHeader>
              <CardTitle>{user?.full_name}</CardTitle>
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
              <div className="flex gap-2">
                <Button
                  data-testid="lang-spanish-btn"
                  variant={i18n.language === 'es' ? 'default' : 'outline'}
                  onClick={() => changeLanguage('es')}
                  className={i18n.language === 'es' ? 'btn-primary' : ''}
                >
                  {t('settings.spanish')}
                </Button>
                <Button
                  data-testid="lang-english-btn"
                  variant={i18n.language === 'en' ? 'default' : 'outline'}
                  onClick={() => changeLanguage('en')}
                  className={i18n.language === 'en' ? 'btn-primary' : ''}
                >
                  {t('settings.english')}
                </Button>
              </div>
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
