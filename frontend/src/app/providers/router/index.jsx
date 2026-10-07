import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { MainLayout } from '../MainLayout'; 
import { HomePage } from '../../../pages/home/HomePage';
import { LoginPage } from '../../../pages/login/LoginPage';
import { RegisterPage } from '../../../pages/register/RegisterPage';
import { ForumPage } from '../../../pages/forum/ForumPage';
import { ForumTopicsPage } from '../../../pages/forum/ForumTopicsPage';
import { CharactersPage } from '../../../pages/characters/CharactersPage';
import { ProtectedRoute } from './ProtectedRoute';
import { VisitTracker } from '../VisitTracker';
import { ForumLoginPage } from '../../../pages/forum/ForumLoginPage';
import { CreateTopicPage } from '../../../pages/forum/CreateTopicPage';
import { TopicCommentsPage } from '../../../pages/forum/TopicCommentsPage';
import { ConfirmResetPasswordPage } from '../../../pages/confirm-reset-password/ConfirmResetPasswordPage';
import { ResetPasswordPage } from '../../../pages/reset-password/ResetPasswordPage';
import { CharacterInfoPage } from '../../../pages/characters-info/CharacterInfoPage';
import { CharacterSearchPage } from '../../../pages/characters-search/CharactersSearchPage';
import { CharacterAttachmentPage } from '../../../pages/characters-attachment/CharacterAttachmentPage';
import { CharacterDetachmentPage } from '../../../pages/characters-detachment/CharacterDetachmentPage';
import { CharacterCreationPage } from '../../../pages/characters-creation/CharacterCreationPage';
import { CharacterTransferPage } from '../../../pages/characters-transfer/CharacterTransferPage';
import LocationContainer from '../../locations/LocationContainer';
import AdminPage from '../../../pages/admin/AdminPage';

export const AppRouter = () => {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={
          <VisitTracker>
            <HomePage />
          </VisitTracker>
        } />
        <Route path="/login" element={
          <VisitTracker>
            <LoginPage />
          </VisitTracker>
        } />
        <Route path="/register" element={
          <VisitTracker>
            <RegisterPage />
          </VisitTracker>
        } />
        <Route path="/forum" element={
          <VisitTracker>
            <ForumPage />
          </VisitTracker>
        } />
        <Route path="/forum/:forumId/topics" element={
          <VisitTracker>
            <ForumTopicsPage />
          </VisitTracker>
        } />

        <Route
          path="/characters"
          element={
            <ProtectedRoute>
              <CharactersPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/characters/attach" 
          element={
            <ProtectedRoute>
              <CharacterAttachmentPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/characters/detach" 
          element={
            <ProtectedRoute>
              <CharacterDetachmentPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/characters/create" 
          element={
            <ProtectedRoute>
              <CharacterCreationPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/characters/transfer" 
          element={
            <ProtectedRoute>
              <CharacterTransferPage />
            </ProtectedRoute>
          } 
        />
        <Route path='/characters/search' element={<CharacterSearchPage />} />
        <Route path="/characters/:characterId" element={<CharacterInfoPage />} />

        <Route path="/forum/login" element={<ForumLoginPage />} />
        <Route path="/forum/:forumId/create-topic" element={<CreateTopicPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/confirm-reset-password" element={<ConfirmResetPasswordPage />} />
        
        <Route path="/forum/:forumId/topics/:topicId/comments" 
              element={<TopicCommentsPage />} />
      </Route>


      <Route path="/location" element={
        <ProtectedRoute>
          <LocationContainer />
        </ProtectedRoute>
      } />

      {/* Admin panel */}
      <Route path="/admin" element={
        <ProtectedRoute>
          <AdminPage />
        </ProtectedRoute>
      } />
    </Routes>
  );
};