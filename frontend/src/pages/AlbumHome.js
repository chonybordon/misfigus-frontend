import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ArrowLeft, Users, Package, UserPlus, ExternalLink } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

const maskEmail = (email) => {
  if (!email) return '';
  const [local, domain] = email.split('@');
  if (local.length <= 3) {
    return `${local[0]}***@${domain}`;
  }
  return `${local.substring(0, 3)}***@${domain}`;
};

const getDisplayName = (user, t) => {
  if (!user) return t('app.defaultUser');
  
  // Priority 1: Display name if exists
  if (user.display_name && user.display_name.trim()) {
    return user.display_name.trim();
  }
  
  // Priority 2: Check for test/demo accounts
  if (user.email) {
    const prefix = user.email.split('@')[0].trim().toLowerCase();
    
    const testMappings = {
      'user': t('members.testUser'),
      'newuser': t('members.newTestUser'),
      'testuser': t('members.testUser'),
      'test': t('members.testUser'),
      'demo': t('members.testUser'),
      'testactivation': t('members.technicalAccount')
    };
    
    if (testMappings[prefix]) {
      return testMappings[prefix];
    }
    
    // Priority 3: Masked email
    return maskEmail(user.email);
  }
  
  return t('app.defaultUser');
};

export const AlbumHome = () => {
  const { albumId } = useParams();
  const [album, setAlbum] = useState(null);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [membersDialogOpen, setMembersDialogOpen] = useState(false);
  const [inviteLink, setInviteLink] = useState('');
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchAlbum();
  }, [albumId]);

  const fetchAlbum = async () => {
    try {
      const response = await api.get(`/albums/${albumId}`);
      setAlbum(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
      navigate('/albums');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateInvite = async () => {
    try {
      const response = await api.post(`/albums/${albumId}/invites`);
      const link = `${window.location.origin}/join/${response.data.token}`;
      setInviteLink(link);
      toast.success(t('invite.generate'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(inviteLink);
      toast.success(t('invite.copied'));
    } catch (error) {
      console.log('Clipboard API not available, user can select manually');
    }
  };

  const handleSelectLink = () => {
    const input = document.getElementById('invite-link-input');
    if (input) {
      input.select();
    }
  };

  const handleOpenInNewTab = () => {
    window.open(inviteLink, '_blank');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen sticker-album-pattern">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button
            data-testid="back-to-albums-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/albums')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-black tracking-tight text-primary">{album?.name}</h1>
            <p className="text-muted-foreground">
              {album?.member_count} {t('albumHome.members')}
            </p>
          </div>
        </div>

        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold">{t('albumHome.progress')}</span>
            <span className="text-sm font-bold text-primary">{album?.progress}%</span>
          </div>
          <Progress value={album?.progress || 0} className="h-3" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <Card
            data-testid="inventory-card"
            className="hover:shadow-lg transition-all cursor-pointer border-2 hover:border-primary"
            onClick={() => navigate(`/albums/${albumId}/inventory`)}
          >
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                {t('albumHome.myInventory')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {t('albumHome.manageInventory')}
              </p>
            </CardContent>
          </Card>

          <Card
            data-testid="matches-card"
            className="hover:shadow-lg transition-all cursor-pointer border-2 hover:border-primary"
            onClick={() => navigate(`/albums/${albumId}/matches`)}
          >
            <CardHeader>
              <CardTitle>{t('albumHome.matches')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {t('albumHome.findTrades')}
              </p>
            </CardContent>
          </Card>
        </div>

        <Card data-testid="members-card" className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              {t('albumHome.members')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {album?.members?.map((member) => (
                <div key={member.id} className="flex items-center gap-2 p-2 rounded-lg bg-muted">
                  <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm">
                    {getDisplayName(member, t)[0].toUpperCase()}
                  </div>
                  <span className="text-sm font-medium truncate">{getDisplayName(member, t)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
          <DialogTrigger asChild>
            <Button
              data-testid="invite-member-btn"
              className="w-full btn-secondary"
            >
              <UserPlus className="h-5 w-5 mr-2" />
              {t('albumHome.invite')}
            </Button>
          </DialogTrigger>
          <DialogContent data-testid="invite-dialog">
            <DialogHeader>
              <DialogTitle>{t('invite.title')}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">{t('invite.subtitle')}</p>
              
              {!inviteLink ? (
                <Button
                  data-testid="generate-invite-btn"
                  onClick={handleGenerateInvite}
                  className="w-full btn-primary"
                >
                  {t('invite.generate')}
                </Button>
              ) : (
                <div className="space-y-3">
                  <div>
                    <input
                      id="invite-link-input"
                      data-testid="invite-link-input"
                      type="text"
                      value={inviteLink}
                      readOnly
                      className="w-full p-3 border rounded-lg text-sm bg-muted font-mono"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <Button
                      data-testid="copy-invite-btn"
                      onClick={handleCopyLink}
                      variant="outline"
                      size="sm"
                    >
                      {t('invite.copy')}
                    </Button>
                    <Button
                      data-testid="select-invite-btn"
                      onClick={handleSelectLink}
                      variant="outline"
                      size="sm"
                    >
                      {t('invite.select')}
                    </Button>
                    <Button
                      data-testid="open-invite-btn"
                      onClick={handleOpenInNewTab}
                      variant="outline"
                      size="sm"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs space-y-1">
                    <p>• {t('invite.expires')}</p>
                    <p>• {t('invite.singleUse')}</p>
                  </div>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AlbumHome;
