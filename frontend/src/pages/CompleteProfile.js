import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { User } from 'lucide-react';

export const CompleteProfile = ({ onComplete }) => {
  const [displayName, setDisplayName] = useState('');
  const [saving, setSaving] = useState(false);
  const { t } = useTranslation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!displayName.trim()) {
      return;
    }
    
    setSaving(true);
    try {
      const response = await api.patch('/auth/me', {
        display_name: displayName.trim()
      });
      
      // Update cached user data
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      const updatedUser = { ...currentUser, display_name: displayName.trim() };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      // Call the completion callback
      onComplete(updatedUser);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen sticker-album-pattern flex items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <User className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-2xl">{t('profile.completeTitle')}</CardTitle>
          <CardDescription>{t('profile.completeSubtitle')}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                {t('profile.enterName')}
              </label>
              <Input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder={t('profile.namePlaceholder')}
                className="mt-1"
                autoFocus
                maxLength={50}
              />
            </div>
            <Button
              type="submit"
              className="w-full btn-primary"
              disabled={!displayName.trim() || saving}
            >
              {saving ? t('common.loading') : t('profile.continueBtn')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default CompleteProfile;
