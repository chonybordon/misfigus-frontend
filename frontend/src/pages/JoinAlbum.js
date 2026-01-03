import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, AuthContext } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, CheckCircle } from 'lucide-react';

export const JoinAlbum = () => {
  const { token } = useParams();
  const { user } = useContext(AuthContext);
  const [invite, setInvite] = useState(null);
  const [album, setAlbum] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    if (!user) {
      localStorage.setItem('pendingInvite', token);
      navigate('/');
      return;
    }
    
    fetchInvite();
  }, [token, user]);

  const fetchInvite = async () => {
    try {
      const response = await api.get(`/invites/${token}`);
      setInvite(response.data.invite);
      setAlbum(response.data.album);
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (detail === 'Invite expired') {
        setError(t('invite.expired'));
      } else if (detail === 'Invite already used') {
        setError(t('invite.used'));
      } else {
        setError(t('invite.invalid'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async () => {
    setAccepting(true);
    try {
      await api.post(`/invites/${token}/accept`);
      toast.success(t('common.success'));
      navigate(`/albums/${album.id}`);
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (detail === 'Already a member') {
        toast.info('Ya eres miembro de este álbum');
        navigate(`/albums/${album.id}`);
      } else {
        toast.error(error.response?.data?.detail || t('common.error'));
      }
    } finally {
      setAccepting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center sticker-album-pattern">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center sticker-album-pattern p-4">
      <Card className="max-w-md w-full">
        <CardHeader>
          <CardTitle className="text-2xl text-center">
            {error ? t('common.error') : t('invite.accept')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="text-center space-y-4">
              <AlertCircle className="h-16 w-16 mx-auto text-destructive" />
              <p className="text-lg">{error}</p>
              <Button onClick={() => navigate('/albums')} className="w-full">
                {t('common.back')}
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-center">
                <CheckCircle className="h-16 w-16 mx-auto text-green-500 mb-4" />
                <h3 className="text-xl font-bold mb-2">{album?.name}</h3>
                <p className="text-muted-foreground">
                  {album?.year} • {album?.category}
                </p>
              </div>
              <div className="bg-muted p-4 rounded-lg space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>{t('invite.expires')}:</span>
                  <span className="font-semibold">1 hora</span>
                </div>
                <div className="flex justify-between">
                  <span>{t('invite.singleUse')}:</span>
                  <span className="font-semibold">✓</span>
                </div>
              </div>
              <Button
                data-testid="accept-invite-btn"
                onClick={handleAccept}
                disabled={accepting}
                className="w-full btn-primary"
              >
                {accepting ? t('invite.accepting') : t('invite.accept')}
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate('/albums')}
                className="w-full"
              >
                {t('common.cancel')}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default JoinAlbum;
