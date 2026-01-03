import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Users, BookOpen, UserPlus, Copy } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

export const GroupHome = () => {
  const { groupId } = useParams();
  const [group, setGroup] = useState(null);
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteLink, setInviteLink] = useState('');
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchGroupData();
  }, [groupId]);

  const fetchGroupData = async () => {
    try {
      const [groupRes, albumsRes] = await Promise.all([
        api.get(`/groups/${groupId}`),
        api.get(`/albums?group_id=${groupId}`),
      ]);
      setGroup(groupRes.data);
      setAlbums(albumsRes.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateInvite = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post(`/groups/${groupId}/invites`, {
        group_id: groupId,
        invited_email: inviteEmail || null,
      });
      const link = `${window.location.origin}/join/${response.data.token}`;
      setInviteLink(link);
      toast.success(t('groupHome.inviteSuccess'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  const copyInviteLink = () => {
    navigator.clipboard.writeText(inviteLink);
    toast.success(t('groupHome.linkCopied'));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button
            data-testid="back-to-groups-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/groups')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-4xl font-black tracking-tight text-primary">{group?.name}</h1>
            <p className="text-muted-foreground mt-1">
              {group?.member_count} {t('groupHome.members')}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card data-testid="members-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                {t('groupHome.members')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {group?.members?.map((member) => (
                  <div key={member.id} className="flex items-center gap-2 p-2 rounded-lg bg-muted">
                    <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      {member.full_name[0].toUpperCase()}
                    </div>
                    <span className="text-sm font-medium">{member.full_name}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="md:col-span-2" data-testid="albums-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                {t('groupHome.albums')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {albums.map((album) => (
                  <div key={album.id} className="border-2 rounded-lg p-4 hover:border-primary transition-all cursor-pointer"
                    onClick={() => navigate(`/groups/${groupId}/albums/${album.id}/inventory`)}>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-bold text-lg">{album.name}</h3>
                      <span className="text-sm text-muted-foreground">{album.year}</span>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        data-testid={`view-inventory-btn-${album.id}`}
                        size="sm"
                        className="btn-primary"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/groups/${groupId}/albums/${album.id}/inventory`);
                        }}
                      >
                        {t('inventory.title')}
                      </Button>
                      <Button
                        data-testid={`view-matches-btn-${album.id}`}
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/groups/${groupId}/albums/${album.id}/matches`);
                        }}
                      >
                        {t('matches.title')}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card data-testid="offers-card">
          <CardHeader>
            <CardTitle>{t('offers.title')}</CardTitle>
          </CardHeader>
          <CardContent>
            <Button
              data-testid="view-offers-btn"
              className="btn-primary"
              onClick={() => navigate(`/groups/${groupId}/offers`)}
            >
              {t('offers.title')}
            </Button>
          </CardContent>
        </Card>

        <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
          <DialogTrigger asChild>
            <Button
              data-testid="invite-member-btn"
              className="fixed bottom-8 right-8 h-14 px-6 rounded-full shadow-2xl btn-secondary"
            >
              <UserPlus className="h-5 w-5 mr-2" />
              {t('groupHome.invite')}
            </Button>
          </DialogTrigger>
          <DialogContent data-testid="invite-dialog">
            <DialogHeader>
              <DialogTitle>{t('groupHome.inviteTitle')}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleGenerateInvite} className="space-y-4">
              <Input
                data-testid="invite-email-input"
                type="email"
                placeholder={t('groupHome.inviteEmail')}
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
              <Button
                data-testid="generate-invite-btn"
                type="submit"
                className="w-full btn-primary"
              >
                {t('groupHome.generateLink')}
              </Button>
              {inviteLink && (
                <div className="space-y-2">
                  <div className="p-3 bg-muted rounded-lg break-all text-sm">
                    {inviteLink}
                  </div>
                  <Button
                    data-testid="copy-invite-link-btn"
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={copyInviteLink}
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    {t('groupHome.copyLink')}
                  </Button>
                </div>
              )}
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default GroupHome;
